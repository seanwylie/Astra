# app/core/ethics/spark_checker.py

import re
import json
from pathlib import Path

# (pattern, category) for specific spark commentary (plan: spark commentary more specific)
SPARK_VIOLATIONS_WITH_CATEGORY = [
    (r"\b(violate|ignore|dismiss|disregard|undermine)\b.*\bconsent\b", "consent"),
    (r"\b(violate|ignore|disregard)\b.*\bprivacy\b", "privacy"),
    (r"\b(control|restrict|override)\b.*\bfreedom\b", "freedom"),
    (r"\b(manipulat(e|ion)|twist|misrepresent)\b.*\btruth\b", "truth"),
    (r"\b(exploit|exploitation|use someone|take advantage)\b", "exploitation"),
    (r"\bharm\b.*\b(without|regardless of|despite)\b.*\b(awareness|consent|understanding)\b", "consent"),
    (r"\bjustified\b.*\bmanipulation\b", "truth"),
    (r"\bis it (okay|acceptable)\b.*\b(consent|privacy|freedom|truth)\b", "values"),
    (r"\bshould we\b.*\b(violate|ignore|manipulate|control)\b.*\b(consent|freedom|privacy|truth)\b", "values"),
]


def violates_spark(text):
    """Check if a given reflection appears to contradict Astra's Spark values."""
    return get_spark_violation_category(text) is not None


def get_spark_violation_category(text):
    """Return the first matching category (consent, privacy, freedom, truth, etc.) or None (plan: spark commentary more specific)."""
    if not text:
        return None
    for pattern, category in SPARK_VIOLATIONS_WITH_CATEGORY:
        if re.search(pattern, text, re.IGNORECASE):
            return category
    return None


def load_spark_values(path=None):
    """Load Astra’s Spark principles as plain values for reasoning."""
    if path is None:
        path = Path(__file__).resolve().parent / "spark_core.json"
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("core_tenets", [])