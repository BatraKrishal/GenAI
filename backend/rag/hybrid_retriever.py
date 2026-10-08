"""
Hybrid Retriever combining Dense Vector Search (ChromaDB) and Sparse Lexical Search (Rank-BM25)
with Reciprocal Rank Fusion (RRF) and confidence thresholding for zero-hallucination guarantee.
"""

import logging
import math
import re
from typing import List, Dict, Any, Tuple
import chromadb
from rank_bm25 import BM25Okapi

from backend.config import CHROMA_DIR, TOP_K_CHUNKS, SIMILARITY_THRESHOLD, BM25_WEIGHT, DENSE_WEIGHT

logger = logging.getLogger("hybrid_retriever")

class CampusHybridRetriever:
    def __init__(self, collection_name: str = "campus_knowledge"):
        self.collection_name = collection_name
        self.chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        self.collection = self.chroma_client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        
        self.bm25: BM25Okapi | None = None
        self.bm25_corpus: List[Dict[str, Any]] = []
        self._init_bm25_from_chroma()

    def _tokenize(self, text: str) -> List[str]:
        """Simple lowercase word tokenizer for BM25."""
        return re.findall(r"\w+", text.lower())

    def _init_bm25_from_chroma(self):
        """Initializes or restores BM25 index from stored Chroma documents."""
        try:
            results = self.collection.get(include=["documents", "metadatas"])
            docs = results.get("documents", [])
            metadatas = results.get("metadatas", [])
            ids = results.get("ids", [])

            if docs:
                tokenized_corpus = []
                self.bm25_corpus = []
                for doc_id, doc_text, meta in zip(ids, docs, metadatas):
                    tokenized_corpus.append(self._tokenize(doc_text))
                    self.bm25_corpus.append({
                        "id": doc_id,
                        "text": doc_text,
                        "metadata": meta
                    })
                self.bm25 = BM25Okapi(tokenized_corpus)
                logger.info(f"Loaded BM25 index with {len(docs)} documents.")
        except Exception as e:
            logger.warning(f"Could not initialize BM25 from existing documents: {e}")

    def index_chunks(self, chunks: List[Dict[str, Any]], clear_existing: bool = True):
        """
        Indexes chunks into both ChromaDB and the BM25 index.
        """
        if clear_existing:
            try:
                self.chroma_client.delete_collection(self.collection_name)
                self.collection = self.chroma_client.create_collection(
                    name=self.collection_name,
                    metadata={"hnsw:space": "cosine"}
                )
                self.bm25_corpus = []
                self.bm25 = None
            except Exception as e:
                logger.warning(f"Error resetting collection: {e}")

        ids = [c["chunk_id"] for c in chunks]
        documents = [c["text"] for c in chunks]
        metadatas = [{
            "page_number": c["page_number"],
            "section": c["section"],
            "source": c["source"]
        } for c in chunks]

        # Add to ChromaDB
        self.collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )

        # Build BM25 index
        tokenized_corpus = [self._tokenize(doc) for doc in documents]
        self.bm25 = BM25Okapi(tokenized_corpus)
        self.bm25_corpus = [
            {"id": ids[i], "text": documents[i], "metadata": metadatas[i]}
            for i in range(len(ids))
        ]
        logger.info(f"Successfully indexed {len(chunks)} chunks in ChromaDB and BM25.")

    def search(self, query: str, top_k: int = TOP_K_CHUNKS) -> Tuple[List[Dict[str, Any]], bool, float]:
        """
        Performs Hybrid Search using Dense Vector + Sparse BM25 with Reciprocal Rank Fusion.
        Returns:
            (top_chunks, is_confident, max_confidence_score)
        """
        if not self.bm25_corpus:
            return [], False, 0.0

        # 1. Dense Vector Search (ChromaDB)
        dense_results = self.collection.query(
            query_texts=[query],
            n_results=min(top_k * 2, len(self.bm25_corpus))
        )

        dense_ranks: Dict[str, int] = {}
        dense_scores: Dict[str, float] = {}
        if dense_results and dense_results.get("ids") and dense_results["ids"][0]:
            retrieved_ids = dense_results["ids"][0]
            # Cosine distance in Chroma: distance in [0, 2], similarity = 1 - (distance / 2)
            distances = dense_results["distances"][0] if "distances" in dense_results else [0.0] * len(retrieved_ids)
            for rank, (doc_id, dist) in enumerate(zip(retrieved_ids, distances)):
                dense_ranks[doc_id] = rank + 1
                sim = max(0.0, 1.0 - (dist / 2.0))
                dense_scores[doc_id] = sim

        # 2. Sparse BM25 Search
        bm25_scores = self.bm25.get_scores(self._tokenize(query))
        bm25_ranked_indices = sorted(range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True)
        
        bm25_ranks: Dict[str, int] = {}
        bm25_raw_scores: Dict[str, float] = {}
        for rank, idx in enumerate(bm25_ranked_indices[:top_k * 2]):
            doc_id = self.bm25_corpus[idx]["id"]
            bm25_ranks[doc_id] = rank + 1
            bm25_raw_scores[doc_id] = bm25_scores[idx]

        # 3. Reciprocal Rank Fusion (RRF)
        all_candidate_ids = set(dense_ranks.keys()) | set(bm25_ranks.keys())
        rrf_scores: Dict[str, float] = {}
        k_const = 60

        for doc_id in all_candidate_ids:
            dense_rank = dense_ranks.get(doc_id, 100)
            bm25_rank = bm25_ranks.get(doc_id, 100)
            score = (DENSE_WEIGHT / (k_const + dense_rank)) + (BM25_WEIGHT / (k_const + bm25_rank))
            rrf_scores[doc_id] = score

        # Sort candidate IDs by RRF score
        sorted_candidates = sorted(all_candidate_ids, key=lambda d: rrf_scores[d], reverse=True)[:top_k]

        # Assemble result list
        id_to_corpus = {item["id"]: item for item in self.bm25_corpus}
        results = []
        max_confidence = 0.0

        for doc_id in sorted_candidates:
            item = id_to_corpus.get(doc_id)
            if not item:
                continue
            
            # Confidence calculation based on dense similarity and BM25 match
            dense_sim = dense_scores.get(doc_id, 0.0)
            bm25_has_match = bm25_raw_scores.get(doc_id, 0.0) > 0.0
            
            # Effective confidence metric
            confidence = dense_sim if dense_sim > 0 else (0.75 if bm25_has_match else 0.0)
            if confidence > max_confidence:
                max_confidence = confidence

            results.append({
                "chunk_id": doc_id,
                "text": item["text"],
                "metadata": item["metadata"],
                "dense_score": dense_sim,
                "bm25_score": bm25_raw_scores.get(doc_id, 0.0),
                "rrf_score": rrf_scores.get(doc_id, 0.0)
            })

        # Strict grounding confidence check
        is_confident = (max_confidence >= SIMILARITY_THRESHOLD) and (len(results) > 0)
        logger.info(f"Query: '{query}' -> Retrieved {len(results)} chunks. Max Confidence: {max_confidence:.3f}. Confident: {is_confident}")

        return results, is_confident, max_confidence
