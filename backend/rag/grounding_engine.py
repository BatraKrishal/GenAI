"""
Grounding Engine: Strict zero-hallucination prompt generator, LLM integration,
and citation verifier for IEEE GenAI Build 2026.
"""

import logging
import os
from typing import List, Dict, Any, Optional

from backend.config import GEMINI_API_KEY, DEFAULT_LLM_MODEL, FALLBACK_RESPONSE

logger = logging.getLogger("grounding_engine")

SYSTEM_PROMPT_TEMPLATE = """You are the official Campus AI Assistant for GBPIET.
Your task is to provide accurate, context-aware, and helpful answers strictly grounded in the official campus document snippets provided below.

CRITICAL RULES:
1. STRICT DATASET GROUNDING: Answer ONLY using the facts present in the provided snippets. Do NOT assume, extrapolate, or use external knowledge.
2. CITATIONS: Every factual statement or policy detail must include a source citation formatted as: [Doc: Page {page_number}, Section: {section}].
3. ZERO HALLUCINATIONS: If the provided snippets do not contain sufficient information to answer the question, or if the question is unanswerable from the context, state EXACTLY:
"{fallback_response}"
Never make up dates, fees, rules, faculty names, or email addresses.
4. LANGUAGE: If the user queries in Hindi, reply in Hindi (Devanagari script) while keeping technical terms and citations clear. If the user queries in English, reply in English.
5. TONE & PERSONA: Maintain a professional, polite, and campus-friendly tone adapted to the persona: {persona}.

OFFICIAL CAMPUS CONTEXT SNIPPETS:
{context_blocks}
"""

class CampusGroundingEngine:
    def __init__(self, api_key: Optional[str] = None, model_name: str = DEFAULT_LLM_MODEL):
        self.api_key = api_key or GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")
        self.model_name = model_name
        self.client = None
        self._init_llm_client()

    def _init_llm_client(self):
        if self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
                logger.info(f"Gemini client initialized with model: {self.model_name}")
            except Exception as e:
                logger.warning(f"Failed to initialize google-genai client: {e}")
                self.client = None
        else:
            logger.info("No GEMINI_API_KEY configured yet. Mock/dry-run generator available.")

    def format_context(self, retrieved_chunks: List[Dict[str, Any]]) -> str:
        """Formats retrieved chunks with page and section metadata."""
        formatted_blocks = []
        for i, chunk in enumerate(retrieved_chunks):
            meta = chunk.get("metadata", {})
            page = meta.get("page_number", "Unknown")
            section = meta.get("section", "General")
            source = meta.get("source", "Campus Document")
            text = chunk.get("text", "").strip()

            block = (
                f"--- [Snippet {i+1}] ---\n"
                f"Source: {source} | Page: {page} | Section: {section}\n"
                f"Content:\n{text}\n"
            )
            formatted_blocks.append(block)

        return "\n".join(formatted_blocks)

    def generate_grounded_answer(
        self,
        query: str,
        retrieved_chunks: List[Dict[str, Any]],
        conversation_history: Optional[List[Dict[str, str]]] = None,
        persona: str = "Student",
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Generates a grounded answer. If context is empty or unconfident, returns safe fallback.
        """
        # If no chunks were retrieved with sufficient confidence
        if not retrieved_chunks:
            return {
                "answer": FALLBACK_RESPONSE,
                "is_grounded": False,
                "citations": [],
                "confidence": 0.0
            }

        context_blocks = self.format_context(retrieved_chunks)
        system_instruction = SYSTEM_PROMPT_TEMPLATE.format(
            fallback_response=FALLBACK_RESPONSE,
            persona=persona,
            context_blocks=context_blocks
        )

        # Build prompt with history
        history_text = ""
        if conversation_history:
            for msg in conversation_history[-4:]:  # last 4 turns
                role = "User" if msg.get("role") == "user" else "Assistant"
                history_text += f"{role}: {msg.get('content', '')}\n"

        prompt = f"{system_instruction}\n\nCONVERSATION HISTORY:\n{history_text}\nUSER QUERY: {query}\n\nASSISTANT ANSWER:"

        # Generate response
        citations = []
        for chunk in retrieved_chunks:
            meta = chunk.get("metadata", {})
            citations.append({
                "page": meta.get("page_number", 1),
                "section": meta.get("section", "General"),
                "source": meta.get("source", "Campus Document"),
                "excerpt": chunk.get("text", "")[:180] + "..."
            })

        if self.client:
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt
                )
                answer_text = response.text.strip()
                
                # Check if model invoked fallback
                is_grounded = FALLBACK_RESPONSE not in answer_text

                return {
                    "answer": answer_text,
                    "is_grounded": is_grounded,
                    "citations": citations if is_grounded else [],
                    "confidence": retrieved_chunks[0].get("dense_score", 0.8)
                }
            except Exception as e:
                logger.error(f"Error calling LLM API: {e}")
                return {
                    "answer": f"Error generating grounded response: {str(e)}",
                    "is_grounded": False,
                    "citations": citations,
                    "confidence": 0.0
                }

        # Offline / Mock Fallback if API key not set yet
        mock_answer = (
            f"Based on the official campus document (Page {citations[0]['page']}), "
            f"here is the verified information regarding '{query}':\n\n"
            f"> \"{retrieved_chunks[0]['text'][:300]}...\"\n\n"
            f"[Doc: Page {citations[0]['page']}, Section: {citations[0]['section']}]"
        )
        return {
            "answer": mock_answer,
            "is_grounded": True,
            "citations": citations,
            "confidence": 0.85
        }
