# IEEE GenAI Build 2026: Campus Chatbot Implementation Plan

> **Target:** 100/100 Base Score + 15/15 Bonus Marks (Total: 115/100)  
> **Event:** IEEE Student Branch GBPIET – GenAI Build 2026  
> **Theme:** Build for Campus | Zero-Hallucination Grounded RAG Chatbot

---

## 1. Executive Summary & Scoring Strategy

The competition evaluates technical depth, strict dataset grounding, originality, and user experience. Cloned turnkey platforms (such as RAGFlow, Dify, etc.) lead to **immediate disqualification**. To win, we must build a **custom, modular, and demonstrable RAG system** tailored to the evaluation rubric.

| Evaluation Criteria | Max Marks | Target Score | Strategy |
| :--- | :--- | :--- | :--- |
| **Technical Complexity & Architecture** | 30 | 30/30 | Hybrid RAG (Dense + BM25), multi-turn memory, query rewriting |
| **Accuracy & Relevance (Grounding)** | 25 | 25/25 | Strict negative constraint prompting, confidence thresholding, verifiable citations |
| **Creativity & Innovation** | 20 | 20/20 | Campus persona switching, dynamic quick-actions, follow-up chips |
| **User Experience & Interface Design** | 10 | 10/10 | Glassmorphic campus theme, interactive citation viewer, responsive UI |
| **Presentation & Technical Defence** | 15 | 15/15 | Pre-structured defense arguments (RAG vs fine-tuning, latency, scaling) |
| **BONUS: Voice Interaction (STT + TTS)** | +10 | +10 | Web Speech API (real-time voice input and speech synthesis) |
| **BONUS: Multilingual & Guardrails** | +5 | +5 | Hindi + English cross-lingual grounding, jailbreak/out-of-scope guardrails |
| **TOTAL** | **100 + 15** | **115/115** | **Clear Winning Submission** |

---

## 2. System Architecture

```
User (Voice / Text)
       │
       ▼
[Frontend UI] ── (Language: English / Hindi)
       │
       ▼
[Layer 1: Input Guardrails & Jailbreak Filter]
       │
       ▼
[Layer 2: Multi-Turn Memory & Query Rewriter]
       │
       ▼
[Layer 3: Hybrid Retrieval Engine]
   ├── ChromaDB / FAISS (Semantic Dense Search)
   └── Rank-BM25 (Exact Acronym / Keyword Search)
       │
       ▼
[Layer 4: Cross-Encoder Reranker & Confidence Thresholding]
   ├── If Confidence < Threshold ──► Fallback: "Information not in official campus doc"
   └── If Confidence >= Threshold ─► Top-K Grounded Chunks
       │
       ▼
[Layer 5: Strict Grounding Prompting + LLM Generation]
       │
       ▼
[Layer 6: Citation Verification & Post-Guardrail]
       │
       ▼
[Frontend Response + Source Page Numbers + TTS Audio Readout]
```

---

## 3. Technology Stack Selection

* **Backend:** FastAPI (Python 3.13)
* **Frontend:** Modern Single-Page App (HTML5 + CSS Glassmorphism + Vanilla JS) or Streamlit with custom CSS
* **Document Ingestion & Parsing:** **Docling (IBM Deep Search)** with layout analysis & table reconstruction + `HybridChunker`
* **Vector Store & Indexing:** ChromaDB / FAISS + Rank-BM25 (Hybrid Dense + Sparse)
* **Embeddings:** `all-MiniLM-L6-v2` / `text-embedding-004`
* **LLM Engine:** Google Gemini API (or Groq / OpenAI with seamless fallback)
* **Voice Engine:** Web Speech API (zero-latency, cross-platform STT + TTS)

---

## 4. Phase-by-Phase Roadmap

### Phase 1: Core Pipeline & Ingestion
1. Project layout setup (`backend/`, `frontend/`, `data/`).
2. Robust PDF parser with page-number tracking and table preservation.
3. Hybrid retriever (Dense + BM25) and similarity thresholding.
4. Strict anti-hallucination prompt template.

### Phase 2: Memory, Voice & Bonus Additions
1. Multi-turn conversation buffer with coreference query re-writing.
2. Voice STT (mic input) and TTS (audio synthesis).
3. Hindi / English bilingual toggle.
4. Input/output safety guardrails.

### Phase 3: Premium UI & Dynamic Ingestion
1. Live file upload endpoint for instant indexing of the official competition PDF (1–2 days prior).
2. Citation inspector modal (click citation to view exact source excerpt & page #).
3. Offline venue resilience checklist.

### Phase 4: Submission Package & Presentation Defense
1. Technical Abstract (`ABSTRACT.md`).
2. Local Setup Guide (`README.md` & `run.bat`).
3. Slide presentation deck & defense talking points.
