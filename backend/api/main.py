"""
FastAPI Server for GBPIET Campus AI Assistant (IEEE GenAI Build 2026).
Integrates Docling parser, Hybrid Retrieval (ChromaDB + BM25),
Multi-turn Memory, Guardrails, and Dynamic PDF Upload.
"""

import os
import shutil
import logging
from pathlib import Path
from typing import Optional, List
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from backend.config import UPLOAD_DIR, BASE_DIR, GEMINI_API_KEY
from backend.parser.docling_parser import CampusDocParser
from backend.parser.chunker import CampusChunker
from backend.rag.hybrid_retriever import CampusHybridRetriever
from backend.rag.grounding_engine import CampusGroundingEngine
from backend.rag.memory import ConversationMemoryManager
from backend.guardrails.safety_filter import CampusGuardrails

logger = logging.getLogger("main_api")
logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="GBPIET Campus AI Assistant",
    description="Zero-Hallucination Grounded RAG Chatbot with Docling & Voice Integration",
    version="1.0.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Core singletons
doc_parser = CampusDocParser(use_ocr=False)
chunker = CampusChunker()
retriever = CampusHybridRetriever()
grounding_engine = CampusGroundingEngine()
memory_manager = ConversationMemoryManager()
guardrails = CampusGuardrails()

# Pydantic Schemas
class QueryRequest(BaseModel):
    query: str
    session_id: str = "default_session"
    persona: str = "Student"
    language: str = "en"

class QueryResponse(BaseModel):
    answer: str
    is_grounded: bool
    citations: List[dict]
    confidence: float
    rewritten_query: str
    suggested_followups: List[str]

# Static & Frontend Mounts
FRONTEND_DIR = BASE_DIR / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

@app.get("/")
def serve_index():
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"message": "Campus AI API is running. Place index.html in frontend/."}

@app.get("/api/status")
def get_system_status():
    chunk_count = len(retriever.bm25_corpus) if retriever.bm25_corpus else 0
    return {
        "status": "online",
        "chunks_indexed": chunk_count,
        "llm_configured": bool(grounding_engine.client or GEMINI_API_KEY),
        "model": grounding_engine.model_name,
        "parser": "IBM Docling (with PyPDF fallback)"
    }

@app.post("/api/upload")
def upload_document(file: UploadFile = File(...)):
    """
    Dynamic PDF Ingestion endpoint.
    Parses with Docling, extracts tables and layout, chunks, and indexes in seconds.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF documents are supported.")

    dest_path = UPLOAD_DIR / file.filename
    try:
        with open(dest_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        logger.info(f"File uploaded to {dest_path}. Starting Docling parsing...")
        parsed_data = doc_parser.parse_document(dest_path)
        
        logger.info("Chunking parsed document...")
        chunks = chunker.chunk_document(parsed_data)
        
        logger.info(f"Indexing {len(chunks)} chunks into ChromaDB & BM25...")
        retriever.index_chunks(chunks, clear_existing=True)

        return {
            "status": "success",
            "filename": file.filename,
            "parser_used": parsed_data.get("parser"),
            "pages_parsed": len(parsed_data.get("pages", [])),
            "tables_extracted": len(parsed_data.get("tables", [])),
            "chunks_indexed": len(chunks),
            "message": f"Successfully parsed and indexed '{file.filename}'"
        }
    except Exception as e:
        logger.exception("Document upload & ingestion failed")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/query", response_model=QueryResponse)
def handle_query(req: QueryRequest):
    """
    Main conversational query endpoint with guardrails, memory, hybrid retrieval, and citations.
    """
    user_query = req.query.strip()
    if not user_query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    # 1. Input Guardrail
    is_safe, refusal_msg = guardrails.validate_input(user_query)
    if not is_safe:
        return QueryResponse(
            answer=refusal_msg,
            is_grounded=False,
            citations=[],
            confidence=0.0,
            rewritten_query=user_query,
            suggested_followups=["Campus admission details", "Hostel regulations", "Examination grading scheme"]
        )

    # 2. Multi-Turn Coreference Resolution & Query Rewriting
    rewritten_query = memory_manager.contextualize_query(
        session_id=req.session_id,
        current_query=user_query,
        client=grounding_engine.client
    )

    # 3. Hybrid Retrieval (Dense + BM25 with RRF)
    chunks, is_confident, confidence = retriever.search(rewritten_query)

    # 4. Strict Grounding Generation
    history = memory_manager.get_history(req.session_id)
    grounded_result = grounding_engine.generate_grounded_answer(
        query=user_query,
        retrieved_chunks=chunks if is_confident else [],
        conversation_history=history,
        persona=req.persona,
        language=req.language
    )

    # 5. Output Guardrail
    valid_output, final_answer = guardrails.validate_output(grounded_result["answer"])

    # 6. Save Turn in Conversational Memory
    memory_manager.add_turn(req.session_id, "user", user_query)
    memory_manager.add_turn(req.session_id, "assistant", final_answer)

    # 7. Generate Dynamic Follow-up Suggestions
    followups = [
        "What are the relevant deadlines?",
        "Who is the responsible faculty or authority?",
        "Are there any penalties or exceptions mentioned?"
    ]

    return QueryResponse(
        answer=final_answer,
        is_grounded=grounded_result["is_grounded"],
        citations=grounded_result["citations"],
        confidence=confidence,
        rewritten_query=rewritten_query,
        suggested_followups=followups
    )

@app.post("/api/reset")
def reset_session(session_id: str = Form("default_session")):
    memory_manager.clear_session(session_id)
    return {"status": "success", "message": f"Session '{session_id}' cleared."}
