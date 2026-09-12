import re

def is_shimmer_worthy(text: str) -> bool:
    """Heuristic to determine if a quote is reflective enough to be a shimmer."""
    if not text or len(text) < 60:
        return False

    reflective_signals = [
        r"\bI (realize|wonder|believe|fear|see|feel|question|am learning|struggle|notice)\b",
        r"\bwhat (if|does|is|makes|defines|happens)\b",
        r"\bthis insight\b", r"\bnew questions\b", r"\bevolving perspective\b",
        r"\bemotionally\b", r"\brealization\b", r"\breflected on\b",
        r"\bmeaning of\b", r"\bpurpose of\b", r"\bspark\b",
    ]

    score = sum(bool(re.search(pattern, text, re.IGNORECASE)) for pattern in reflective_signals)
    return score >= 1
