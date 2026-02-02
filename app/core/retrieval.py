"""
Semantic retrieval for reply context: rank knowledge and reflections by embedding similarity to the user message.
Uses the same SentenceTransformer as question_utils; lazy-loads to avoid import-time cost.
"""

_TRUNCATE = 200
_model = None


def _get_model():
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _model = SentenceTransformer("paraphrase-MiniLM-L6-v2")
        except Exception as e:
            print(f"[retrieval] Model load failed: {e}")
    return _model


def _normalize_entry(entry):
    """Normalize knowledge/reflection entry to string (dict with 'insight' or raw string)."""
    if isinstance(entry, dict):
        return (entry.get("insight") or str(entry)).strip()
    return (entry.strip() if isinstance(entry, str) else str(entry).strip())


def select_relevant_context_semantic(user_message, knowledge_list, reflections_list, top_k=5, top_r=3):
    """
    Select knowledge and reflections by embedding similarity to user_message.
    Returns (knowledge_slice, reflections_slice) or None on failure (caller should fall back to keyword).
    Entries are truncated to _TRUNCATE chars before encoding to keep prompts bounded.
    """
    model = _get_model()
    if model is None or (not knowledge_list and not reflections_list):
        return None
    try:
        import numpy as np
        query = (user_message or "").strip()[:_TRUNCATE]
        if not query:
            return None
        query_emb = model.encode(query, convert_to_tensor=False)
        query_norm = query_emb / (np.linalg.norm(query_emb) + 1e-9)

        knowledge_slice = []
        if knowledge_list:
            texts = [_normalize_entry(e)[:_TRUNCATE] for e in knowledge_list]
            texts = [t for t in texts if t]
            if texts:
                embs = model.encode(texts, convert_to_tensor=False)
                scores = np.dot(embs, query_norm)
                idx = np.argsort(-scores)[:top_k]
                knowledge_slice = [texts[i] for i in idx]

        reflections_slice = []
        if reflections_list:
            texts = [_normalize_entry(r)[:_TRUNCATE] for r in reflections_list]
            texts = [t for t in texts if t]
            if texts:
                embs = model.encode(texts, convert_to_tensor=False)
                scores = np.dot(embs, query_norm)
                idx = np.argsort(-scores)[:top_r]
                reflections_slice = [texts[i] for i in idx]

        return (knowledge_slice, reflections_slice)
    except Exception as e:
        print(f"[retrieval] Semantic selection failed: {e}")
        return None
