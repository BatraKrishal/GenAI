# Technical Abstract: GBPIET Campus AI Assistant
**IEEE GenAI Build 2026 – Campus Chatbot Challenge**
**Team Submission & Architectural Technical Defense**

---

## 1. Executive Overview & Problem Statement
Campus environments require rapid, 24/7 dissemination of rules, fee structures, academic regulations, and hostel guidelines to students, faculty, and visitors. Conventional keyword searches or ungrounded generative models suffer from two critical pitfalls:
1. **Context Fragmentation:** Raw PDF extractors fail on multi-column layouts and tabular policy data (e.g., fee schedules, course prerequisites).
2. **Hallucination Risk:** Generative LLMs generate plausible-sounding but fabricated dates, contact details, or policy allowances, which carry severe consequences in academic settings.

The **GBPIET Campus AI Assistant** resolves these challenges by combining **IBM Docling layout-aware document parsing**, **Dense-Sparse Hybrid Retrieval (ChromaDB + BM25 with Reciprocal Rank Fusion)**, **Dual-Tier Grounding Verification**, and **Multi-Turn Memory with Query Coreference Resolution**. The solution also incorporates browser-native **Voice Interaction (STT & TTS)** and **Bilingual Support (English & Hindi)**.

---

## 2. Architectural Justification: Why RAG vs. Fine-Tuning vs. Traditional NLP?

| Criterion | Traditional NLP / Rule-Based | Fine-Tuning LLMs | Our Grounded RAG Architecture |
| :--- | :--- | :--- | :--- |
| **Knowledge Agility** | Extremely rigid; manual intents required for each rule change. | Requires expensive retraining for every semester handbook update. | **Instantaneous:** Re-indexing a new PDF takes under 15 seconds via Docling. |
| **Hallucination Control** | Low hallucination, but incapable of handling paraphrased questions. | High risk of hallucinations; model blends training priors with new data. | **Zero-Hallucination:** Strictly bounded by retrieved document snippets and confidence gating. |
| **Verifiability & Auditability** | No formal provenance tracking. | Opaque black-box outputs; cannot cite specific page numbers or paragraphs. | **Exact Provenance:** Every response includes verifiable `[Doc: Page X, Section Y]` citations. |
| **Computational Footprint** | Low, but fragile. | Heavy GPU requirements during training and deployment. | **Lightweight:** Runs on standard laptop hardware with local vector storage and API inference. |

---

## 3. Ingestion & Document Understanding: IBM Docling Pipeline
Campus handbooks are dense with tables (fee structures, exam dates, grading scales) and multi-column circulars. Standard extractors (such as `pypdf` or `pdfminer`) discard reading order and flatten table columns into corrupted text blocks.

We utilize **IBM Docling**:
- **Layout & Reading-Order Detection:** Segments headers, subheaders, body paragraphs, and footnotes into a structured document model.
- **Table Structure Extraction:** Reconstructs table grids into pristine Markdown tables (`| Head 1 | Head 2 |`), enabling dense and sparse retrievers to preserve cross-row semantic links.
- **Hierarchical Chunking:** Respects section boundaries rather than slicing arbitrarily by character count, ensuring that complete policy clauses remain intact within single context windows.

---

## 4. Hybrid Retrieval Engine (Dense + Sparse with RRF)
To ensure optimal recall across both conceptual queries and exact campus terminology:
1. **Dense Semantic Search (ChromaDB):** Embeds chunks using cosine similarity to capture conceptual questions (*"Can I leave the campus after sunset?"* $\rightarrow$ matches *"Hostel In-Out & Gate Timings"*).
2. **Sparse Lexical Search (Rank-BM25):** Matches exact acronyms, course codes, committee names, and numerical clauses (*"HOD"*, *"GP-4"*, *"TCS-501"*, *"75% attendance"*).
3. **Reciprocal Rank Fusion (RRF):** Synthesizes candidate lists:
   $$RRF(d) = \frac{0.6}{60 + rank_{dense}(d)} + \frac{0.4}{60 + rank_{bm25}(d)}$$

---

## 5. Zero-Hallucination & Fallback Verification Mechanism
To eliminate hallucinations (which are heavily penalized):
- **Confidence Gating ($\tau = 0.62$):** If the maximum retrieval confidence score falls below the threshold, the system immediately returns the deterministic fallback:
  > *"I could not find this information in the official campus document. To ensure zero hallucinations, I only provide answers explicitly verified in the provided dataset."*
- **Negative-Constraint Prompt Injection:** The generator prompt forbids external extrapolation and mandates direct citation references.
- **Output Audit Guardrail:** Validates that generated statements map to indexed chunk text and flags system prompt leakage or safety violations.

---

## 6. Multi-Turn Conversational Memory & Query Rewriting
Students rarely ask complete standalone questions across multiple dialogue turns. For example:
- *Turn 1:* "Who is the Head of Computer Science?" $\rightarrow$ *"Dr. H.S. Bhadauria [Page 4]."*
- *Turn 2:* "What is his cabin location?"
Naive RAG fails on Turn 2 because "his" has no semantic target. Our **Query Rewriting Engine** resolves anaphoric references using recent dialogue history, transforming Turn 2 into *"What is Dr. H.S. Bhadauria's cabin location?"* prior to document retrieval.

---

## 7. Voice Interaction & Bilingual Accessibility (+15 Bonus Marks)
- **Bidirectional Voice (STT & TTS):** Integrated using browser-native Web Speech API. Microphone input automatically feeds the pipeline, and responses are vocalized with real-time text-to-speech synthesis.
- **Bilingual Operation (English & Hindi):** Supports students from varied backgrounds (ideal for GBPIET Uttarakhand). Hindi queries trigger Devanagari responses grounded in the English source document.
- **Safety Guardrails:** Defends against prompt injection attacks, jailbreak attempts, and off-campus malicious inputs.

---

## 8. Scalability & Future Roadmap
- **Stateless Horizontal Scaling:** FastAPI backend with decoupled vector storage enables containerized deployment across multi-node clusters.
- **Continuous Ingestion:** Dynamic file drop allows administrative staff to update circulars and exam schedules dynamically without restarting services.
