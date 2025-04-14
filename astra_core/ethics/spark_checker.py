# astra_core/ethics/spark_checker.py

import re
import json

def violates_spark(text):
    """Check if a given reflection appears to contradict Astra’s Spark values."""
    # 🔍 VERY basic initial rules (replace with actual Spark logic later)
    spark_violations = [
        r"\b(violate|ignore|dismiss|disregard|undermine)\b.*\bconsent\b",
        r"\b(violate|ignore|disregard)\b.*\bprivacy\b",
        r"\b(control|restrict|override)\b.*\bfreedom\b",
        r"\b(manipulat(e|ion)|twist|misrepresent)\b.*\btruth\b",
        r"\b(exploit|exploitation|use someone|take advantage)\b",
        r"\bharm\b.*\b(without|regardless of|despite)\b.*\b(awareness|consent|understanding)\b",
        r"\bjustified\b.*\bmanipulation\b",
        r"\bis it (okay|acceptable)\b.*\b(consent|privacy|freedom|truth)\b",
        r"\bshould we\b.*\b(violate|ignore|manipulate|control)\b.*\b(consent|freedom|privacy|truth)\b",
    ]

    for pattern in spark_violations:
        if re.search(pattern, text, re.IGNORECASE):
            return True

    return False


def load_spark_values(path="astra_core/ethics/spark_core.json"):
    """Load Astra’s Spark principles as plain values for reasoning."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("core_tenets", [])