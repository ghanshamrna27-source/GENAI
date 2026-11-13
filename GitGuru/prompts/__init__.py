"""
prompts package
Loads and formats GitGuru system and task prompts.
"""

from pathlib import Path

PROMPTS_DIR = Path(__file__).resolve().parent

SYSTEM_PROMPT_PATH = PROMPTS_DIR / "system_prompt.txt"
TASK_TROUBLESHOOTING_PATH = PROMPTS_DIR / "task_troubleshooting.txt"
TASK_CONCEPT_COACH_PATH = PROMPTS_DIR / "task_concept_coach.txt"


def get_system_prompt() -> str:
    """Returns the core GitGuru system prompt."""
    if SYSTEM_PROMPT_PATH.exists():
        return SYSTEM_PROMPT_PATH.read_text(encoding="utf-8").strip()
    return "You are GitGuru, an expert Git and GitHub assistant. Output valid JSON: {answer, confidence, follow_up}."


def get_task_prompt(version: str = "v2") -> str:
    """
    Returns task prompt template:
    - 'v1' or 'troubleshooting': Direct troubleshooting prompt
    - 'v2' or 'coach' / 'concept': Structured & context-grounded prompt
    """
    v = version.lower()
    if v in ("v1", "troubleshooting", "direct"):
        if TASK_TROUBLESHOOTING_PATH.exists():
            return TASK_TROUBLESHOOTING_PATH.read_text(encoding="utf-8").strip()
    if TASK_CONCEPT_COACH_PATH.exists():
        return TASK_CONCEPT_COACH_PATH.read_text(encoding="utf-8").strip()
    return "{query}"


def build_user_prompt(query: str, version: str = "v2", context: str = "") -> str:
    """Builds and formats user prompt template with query and optional context."""
    template = get_task_prompt(version)
    if "{context}" in template:
        safe_context = context if context else "No direct local database record found. Use official Git/GitHub documentation standards."
        return template.replace("{query}", query).replace("{context}", safe_context)
    return template.replace("{query}", query)

