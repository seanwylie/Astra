from difflib import SequenceMatcher

def is_lexical_loop(new_text: str, recent_texts: list[str], threshold: float = 0.92) -> bool:
    for past in recent_texts:
        similarity = SequenceMatcher(None, new_text.strip(), past.strip()).ratio()
        if similarity > threshold:
            print(f"🌀 Loop Detected: {similarity * 100:.1f}% similarity with past reflection")
            return True
    return False
