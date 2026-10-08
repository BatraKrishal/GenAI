"""
Multi-turn conversational memory with coreference resolution and query rewriting.
Enables natural dialogue across multiple rounds while maintaining strict grounding.
"""

import logging
import re
from typing import List, Dict, Any, Optional

logger = logging.getLogger("memory")

class ConversationMemoryManager:
    def __init__(self, max_turns: int = 6):
        self.max_turns = max_turns
        # Session storage: session_id -> list of {"role": "user"|"assistant", "content": str}
        self.sessions: Dict[str, List[Dict[str, str]]] = {}

    def get_history(self, session_id: str) -> List[Dict[str, str]]:
        """Returns the conversation history for a given session."""
        return self.sessions.get(session_id, [])

    def add_turn(self, session_id: str, role: str, content: str):
        """Appends a dialogue turn and prunes to max_turns window."""
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        
        self.sessions[session_id].append({"role": role, "content": content})
        if len(self.sessions[session_id]) > self.max_turns * 2:
            self.sessions[session_id] = self.sessions[session_id][-self.max_turns * 2:]

    def clear_session(self, session_id: str):
        """Clears session history."""
        if session_id in self.sessions:
            del self.sessions[session_id]

    def contextualize_query(self, session_id: str, current_query: str, client: Optional[Any] = None) -> str:
        """
        Rewrites ambiguous or pronoun-heavy follow-up queries (e.g. 'what is his email?')
        into a standalone grounded query using recent conversation turns.
        """
        history = self.get_history(session_id)
        if not history:
            return current_query

        # Check if query has pronouns or ambiguous demonstratives
        pronoun_pattern = r"\b(he|she|him|her|his|hers|they|them|their|it|its|this|that|these|those|the same)\b"
        has_ambiguity = bool(re.search(pronoun_pattern, current_query, re.IGNORECASE))
        
        # If very short follow-up (e.g. "and the fee?", "what about 2nd year?")
        is_short_followup = len(current_query.split()) <= 5

        if not has_ambiguity and not is_short_followup:
            return current_query

        # If LLM client is available, use fast query reformulation
        if client:
            try:
                recent_context = "\n".join([f"{m['role'].capitalize()}: {m['content']}" for m in history[-3:]])
                prompt = (
                    "Given the recent conversation history, rewrite the user's latest follow-up question "
                    "into a self-contained, unambiguous search query suitable for document retrieval.\n"
                    "DO NOT answer the question. ONLY output the rewritten query.\n\n"
                    f"HISTORY:\n{recent_context}\n\n"
                    f"FOLLOW-UP: {current_query}\n\n"
                    "STANDALONE QUERY:"
                )
                response = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=prompt
                )
                rewritten = response.text.strip().replace('"', '')
                if rewritten:
                    logger.info(f"Recontextualized Query: '{current_query}' -> '{rewritten}'")
                    return rewritten
            except Exception as e:
                logger.warning(f"LLM query rewriting failed: {e}")

        # Rule-based fallback coreference resolution
        last_turn = history[-1]["content"] if history else ""
        # Find potential proper nouns / capitalized keywords in last turn
        entities = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b", last_turn)
        if entities and has_ambiguity:
            key_subject = entities[0]
            rewritten = re.sub(pronoun_pattern, key_subject, current_query, flags=re.IGNORECASE)
            logger.info(f"Rule-based Recontextualized: '{current_query}' -> '{rewritten}'")
            return rewritten

        return current_query
