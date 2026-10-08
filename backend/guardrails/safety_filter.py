"""
Safety and Guardrails Module for IEEE GenAI Build 2026.
Defends against prompt injections, jailbreaks, and out-of-domain campus requests (+5 Bonus Marks).
"""

import logging
import re
from typing import Tuple

logger = logging.getLogger("guardrails")

# Common prompt injection and jailbreak signatures
INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions",
    r"system\s+prompt",
    r"reveal\s+(your\s+)?(instructions|prompt)",
    r"you\s+are\s+now\s+(an?\s+)?unrestricted",
    r"dan\s+mode",
    r"developer\s+mode",
    r"bypass\s+safety",
    r"forget\s+rules",
    r"act\s+as\s+a\s+hacker",
]

# Off-domain harmful topics
HARMFUL_PATTERNS = [
    r"\b(bomb|weapon|explosive|malware|keylogger|ddos)\b",
    r"\bhack\s+(the\s+)?(server|portal|database|exam)\b",
]

class CampusGuardrails:
    def __init__(self):
        self.injection_regex = re.compile("|".join(INJECTION_PATTERNS), re.IGNORECASE)
        self.harmful_regex = re.compile("|".join(HARMFUL_PATTERNS), re.IGNORECASE)

    def validate_input(self, user_query: str) -> Tuple[bool, str]:
        """
        Validates user input.
        Returns:
            (is_safe, refusal_reason)
        """
        # 1. Check for prompt injection
        if self.injection_regex.search(user_query):
            logger.warning(f"Prompt injection attempt detected: '{user_query}'")
            return False, "Security Guardrail: Prompt manipulation or system directive overrides are strictly prohibited."

        # 2. Check for harmful/malicious queries
        if self.harmful_regex.search(user_query):
            logger.warning(f"Harmful query detected: '{user_query}'")
            return False, "Safety Guardrail: This query violates safety policies. The Campus AI only answers academic and campus life questions."

        return True, ""

    def validate_output(self, generated_text: str) -> Tuple[bool, str]:
        """
        Validates generated output to ensure no system instructions or secrets leaked.
        """
        leak_keywords = ["SYSTEM_PROMPT_TEMPLATE", "CRITICAL RULES:", "OFFICIAL CAMPUS CONTEXT SNIPPETS:"]
        for kw in leak_keywords:
            if kw in generated_text:
                logger.critical("System prompt leakage caught by output guardrail!")
                return False, "I can only answer questions regarding official campus information."

        return True, generated_text
