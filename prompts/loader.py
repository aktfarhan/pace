"""Load a versioned prompt from this directory, without its YAML header."""

import re
from pathlib import Path

PROMPTS = Path(__file__).resolve().parent


def load_prompt(name: str) -> str:
    """Reads a prompt file from prompts/ and strips its --- YAML --- header.

    Args:
        name: The prompt filename, e.g. "intent.md".

    Returns:
        The prompt body with the YAML header removed.
    """
    text = (PROMPTS / name).read_text(encoding="utf-8")
    match = re.match(r"^---\r?\n.*?\r?\n---\r?\n(.*)$", text, re.DOTALL)
    return match.group(1).strip() if match else text.strip()
