import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.parser.docling_parser import CampusDocParser
from backend.parser.chunker import CampusChunker
from backend.rag.hybrid_retriever import CampusHybridRetriever

def index_now():
    pdf_path = BASE_DIR / "data" / "uploads" / "gbpiet_campus_handbook_2026.pdf"
    if not pdf_path.exists():
        print("Sample PDF not found.")
        return

    print("Parsing document...")
    parser = CampusDocParser()
    parsed = parser.parse_document(pdf_path)

    print("Chunking...")
    chunker = CampusChunker()
    chunks = chunker.chunk_document(parsed)

    print(f"Indexing {len(chunks)} chunks into ChromaDB & BM25...")
    retriever = CampusHybridRetriever()
    retriever.index_chunks(chunks, clear_existing=True)
    print("Done! Chunks successfully indexed into knowledge base.")

if __name__ == "__main__":
    index_now()
