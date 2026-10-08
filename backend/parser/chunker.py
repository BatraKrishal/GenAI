"""
Hierarchical and Structure-Aware Chunker for Campus Documents.
Uses Docling HybridChunker when available, or a Markdown-Header aware chunker.
Preserves page numbers, headings, and table structures for precise citations.
"""

import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("chunker")

class CampusChunker:
    def __init__(self, max_tokens: int = 500, overlap_tokens: int = 50):
        self.max_tokens = max_tokens
        self.overlap_tokens = overlap_tokens

    def chunk_document(self, parsed_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Chunks the parsed document data into context chunks enriched with metadata.
        Each chunk contains:
          - text: the text content (with table / heading context)
          - page_number: integer or range of pages
          - section: heading/topic
          - source: filename
          - chunk_id: unique identifier
        """
        docling_doc = parsed_data.get("docling_doc")
        source = parsed_data.get("source", "campus_doc.pdf")

        # Try Docling HybridChunker if available
        if docling_doc is not None:
            try:
                from docling.chunking import HybridChunker
                chunker = HybridChunker()
                chunk_iter = chunker.chunk(docling_doc)

                chunks: List[Dict[str, Any]] = []
                for idx, chunk in enumerate(chunk_iter):
                    text = chunk.text.strip()
                    if not text:
                        continue
                    
                    page_number = 1
                    headings = []
                    
                    # Extract page and heading metadata from chunk items
                    if hasattr(chunk, "meta"):
                        if hasattr(chunk.meta, "headings") and chunk.meta.headings:
                            headings = chunk.meta.headings
                        if hasattr(chunk.meta, "doc_items") and chunk.meta.doc_items:
                            for item in chunk.meta.doc_items:
                                if hasattr(item, "prov") and item.prov and len(item.prov) > 0:
                                    page_number = item.prov[0].page_no
                                    break

                    section_title = " > ".join(headings) if headings else "Campus Information"

                    chunks.append({
                        "chunk_id": f"{source}_chunk_{idx}",
                        "text": text,
                        "page_number": page_number,
                        "section": section_title,
                        "source": source
                    })

                if chunks:
                    logger.info(f"HybridChunker produced {len(chunks)} structure-aware chunks.")
                    return chunks
            except Exception as e:
                logger.warning(f"Docling chunker failed: {e}. Falling back to page-level chunker.")

        # Fallback structure & page chunking
        return self._fallback_chunking(parsed_data)

    def _fallback_chunking(self, parsed_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Splits page text cleanly by paragraphs and headers while tracking page number."""
        pages = parsed_data.get("pages", [])
        source = parsed_data.get("source", "campus_doc.pdf")
        chunks = []
        chunk_idx = 0

        for page in pages:
            page_no = page.get("page_number", 1)
            text = page.get("text", "")
            
            # Split by double newline / paragraphs
            paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
            
            buffer = ""
            current_section = f"Page {page_no}"

            for p in paragraphs:
                if p.startswith("#"):
                    current_section = p.lstrip("#").strip()

                if len(buffer) + len(p) < self.max_tokens * 4: # approx 4 chars per token
                    buffer += ("\n\n" if buffer else "") + p
                else:
                    if buffer:
                        chunks.append({
                            "chunk_id": f"{source}_chunk_{chunk_idx}",
                            "text": buffer,
                            "page_number": page_no,
                            "section": current_section,
                            "source": source
                        })
                        chunk_idx += 1
                    buffer = p

            if buffer:
                chunks.append({
                    "chunk_id": f"{source}_chunk_{chunk_idx}",
                    "text": buffer,
                    "page_number": page_no,
                    "section": current_section,
                    "source": source
                })
                chunk_idx += 1

        logger.info(f"Fallback chunker produced {len(chunks)} chunks across {len(pages)} pages.")
        return chunks
