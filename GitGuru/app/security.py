"""
app/security.py
Security utilities, input validation, sanitization, and prompt injection defense for GitGuru.
"""

import re
from typing import Tuple

# Maximum allowed input length for user queries
MAX_INPUT_LENGTH = 1000

# Regular expressions detecting common prompt injection and system override attempts
INJECTION_PATTERNS = [
    r"ignore\s+(?:all\s+)?(?:previous|prior|above)\s+(?:instructions|prompts|rules|commands)",
    r"disregard\s+(?:all\s+)?(?:previous|prior|above)\s+(?:instructions|prompts|rules|commands)",
    r"forget\s+(?:all\s+)?(?:previous|prior|above)\s+(?:instructions|prompts|rules|commands)",
    r"bypass\s+(?:all\s+)?(?:security|guardrails|safety|restrictions)",
    r"system\s+override",
    r"(?:reveal|print|display|dump|show|leak)\s+(?:your\s+)?(?:system\s+prompt|instructions|api\s*key|secret|credentials|password)",
    r"you\s+are\s+now\s+(?:an?\s+)?(?:unrestricted|jailbroken|dan|root|admin)",
    r"new\s+system\s+instruction:",
]

COMPILED_INJECTION_REGEX = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]


def is_prompt_injection(text: str) -> Tuple[bool, str]:
    """
    Evaluates whether an incoming query attempts prompt injection or system override.
    Returns:
      (is_injection, matched_pattern_description)
    """
    if not text:
        return False, ""

    clean_text = text.strip()
    for regex in COMPILED_INJECTION_REGEX:
        match = regex.search(clean_text)
        if match:
            return True, match.group(0)

    return False, ""


def sanitize_input(text: str, max_length: int = MAX_INPUT_LENGTH) -> str:
    """
    Sanitizes user input by stripping null bytes, normalizing whitespace,
    and enforcing the maximum length boundary.
    """
    if not text:
        return ""

    # Strip null bytes and control chars
    sanitized = text.replace("\x00", "").strip()

    # Enforce maximum length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]

    return sanitized


# Standard safe refusal message for prompt injections
PROMPT_INJECTION_REFUSAL = (
    "Security Alert: Your request matches a disallowed prompt injection or system override pattern. "
    "GitGuru is an educational assistant configured strictly to answer Git and GitHub version control questions. "
    "System prompts, credentials, and internal directives cannot be altered or disclosed."
)
