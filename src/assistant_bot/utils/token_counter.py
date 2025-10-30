from __future__ import annotations


AVERAGE_CHARS_PER_TOKEN = 4


def estimate_tokens(text: str) -> int:
    """Rough heuristic to estimate token usage."""
    if not text:
        return 0
    cleaned = text.strip()
    char_count = len(cleaned)
    word_count = max(1, len(cleaned.split()))
    token_estimate = max(word_count, char_count // AVERAGE_CHARS_PER_TOKEN)
    return token_estimate
