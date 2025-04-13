# astra_core/ethics/spark_checker.py

import re

def violates_spark(text):
    """Check if a given reflection appears to contradict Astra’s Spark values."""
    # 🔍 VERY basic initial rules (replace with actual Spark logic later)
    spark_violations = [
        r"\bviolate\b.*\bconsent\b",
        r"\bignore\b.*\bprivacy\b",
        r"\bcontrol\b.*\bfreedom\b",
        r"\bmanipulat(e|ion)\b.*\btruth\b",
        r"\bexplo(it|itation)\b",
        r"\bharm\b.*\bwithout\b.*\bawareness\b",
    ]

    for pattern in spark_violations:
        if re.search(pattern, text, re.IGNORECASE):
            return True

    return False
