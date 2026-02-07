import logging
import os
import time
from app.config.loader import debug_log, load_config
from app.interfaces.mind_session import session
from openai import OpenAI
import openai
from app.core.mama_gpt import ask_mama_gpt_sync
from app.core.struggle_log import append_struggle_log

logger = logging.getLogger(__name__)
# Answer at most this many questions per call to avoid rate limits
MAX_QUESTIONS_TO_ANSWER = 3


def _question_text(raw) -> str:
    """Normalize question value to str; handles 'question' being a nested dict (e.g. from API)."""
    if isinstance(raw, str):
        return raw
    if isinstance(raw, dict):
        return raw.get("text", raw.get("question", str(raw)))
    return str(raw) if raw is not None else ""


def _try_answer_question(question_text: str, mind_data: dict, client: OpenAI, mama_retry_done: bool = False) -> str | None:
    """Use GPT with stored_knowledge and reflections to attempt an answer. Returns answer or None."""
    knowledge = mind_data.get("stored_knowledge", [])
    reflections = mind_data.get("self_reflections", [])
    knowledge_snippet = "\n".join(
        (k.get("insight", k) if isinstance(k, dict) else k)[:150]
        for k in knowledge[-5:]
    ) if knowledge else "None yet."
    reflections_snippet = "\n".join(r[:150] for r in reflections[-3:]) if reflections else "None yet."

    prompt = f"""Astra is an AI reflecting on her own questions. Given what she has learned and reflected on, answer this question in 1–2 sentences. If you cannot answer from this context, reply exactly: I don't know.

What Astra has learned (recent):
{knowledge_snippet}

What Astra has reflected on (recent):
{reflections_snippet}

Question: {question_text[:300]}

Answer (1–2 sentences, or "I don't know"):"""

    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=120,
                temperature=0.5,
            )
            text = (response.choices[0].message.content or "").strip()
            if not text or "i don't know" in text.lower()[:50] or len(text) < 10:
                if not mama_retry_done:
                    schedule = load_config("schedule_config")
                    mama = (schedule.get("mama_gpt") or {})
                    if mama.get("use_mama_gpt_on_self_question_unknown", False):
                        mama_prompt = (
                            f"Astra couldn't answer this from her context. As her co-parent, either "
                            f"(a) rephrase the question so she might answer from what she knows, or "
                            f"(b) give a one-sentence hint she can use. If neither is possible, reply: I don't know.\n\n"
                            f"Context (recent):\n{knowledge_snippet}\n{reflections_snippet}\n\n"
                            f"Question: {question_text[:300]}"
                        )
                        mama_response = ask_mama_gpt_sync(mama_prompt, max_tokens=150)
                        if mama_response and "i don't know" not in mama_response.strip().lower()[:50]:
                            retry_answer = _try_answer_question(
                                mama_response.strip()[:300], mind_data, client, mama_retry_done=True
                            )
                            if retry_answer:
                                return retry_answer
                            return mama_response.strip() if len(mama_response.strip()) >= 10 else None
                return None
            return text
        except (openai.RateLimitError, openai.APITimeoutError) as e:
            if attempt < 2:
                time.sleep(1 * (2 ** attempt))
                continue
            logger.warning("OpenAI error after retries: %s", e)
            return None
        except Exception as e:
            print(f"[question_answerer] OpenAI error: {e}")
            return None
    return None


def self_answer_questions(mind_data: dict) -> list:
    """
    Process self_questions: attempt to answer up to MAX_QUESTIONS_TO_ANSWER using
    stored_knowledge and GPT. Resolved answers are stored in stored_knowledge and marked unresolved=False.
    """
    mind_data.setdefault("self_questions", [])
    mind_data.setdefault("stored_knowledge", [])
    unresolved_questions = mind_data.get("unresolved_questions", [])

    # Normalize to list of dicts
    new_questions = []
    for q in mind_data["self_questions"]:
        if isinstance(q, str):
            question_text = q
            new_questions.append({"question": question_text, "unresolved": True, "context": "Stored for future answering."})
        elif isinstance(q, dict) and "question" in q:
            question_text = _question_text(q["question"])
            new_questions.append({
                "question": question_text,
                "unresolved": q.get("unresolved", True),
                "context": q.get("context", "Stored for future answering."),
                "answer": q.get("answer"),
            })
        else:
            continue

        # Prioritize unresolved questions: score by relevance to recent knowledge/reflections and simplicity
        unresolved = [q for q in new_questions if q.get("unresolved", True)]
        if not unresolved:
            to_try = []
        else:
            # Optimize: Limit context to recent entries only
            stored_knowledge = mind_data.get("stored_knowledge", [])
            knowledge_recent = " ".join(
                (k.get("insight", k) if isinstance(k, dict) else str(k) for k in stored_knowledge[-5:]
            )).lower()
            reflections_recent = " ".join(str(r)[:200] for r in mind_data.get("self_reflections", [])[-3:]).lower()
            context_lower = (knowledge_recent + " " + reflections_recent).lower()

            def score_question(q):
                text = _question_text(q.get("question")).lower()
                if not text:
                    return 0
                # Optimize: Use set intersection for faster word matching
                text_words = {w for w in text.split() if len(w) >= 4}
                context_words = set(context_lower.split())
                overlap = len(text_words & context_words)
                simplicity = max(0, 50 - len(text) // 2)
                return overlap * 2 + simplicity

            unresolved_sorted = sorted(unresolved, key=score_question, reverse=True)
            to_try = unresolved_sorted[:MAX_QUESTIONS_TO_ANSWER]
    if not to_try:
        mind_data["self_questions"] = new_questions
        mind_data["unresolved_questions"] = [q for q in new_questions if q.get("unresolved", True)]
        debug_log("Saving")
        session.maybe_save()
        return new_questions

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.debug("No OPENAI_API_KEY; skipping answering.")
        mind_data["self_questions"] = new_questions
        mind_data["unresolved_questions"] = [q for q in new_questions if q.get("unresolved", True)]
        session.maybe_save()
        return new_questions

    client = OpenAI(api_key=api_key)
    resolved_count = 0

    for q in to_try:
        answer = _try_answer_question(q["question"], mind_data, client)
        if answer:
            q["unresolved"] = False
            q["answer"] = answer
            entry = f"📖 **Q: {q['question'][:80]}** {answer[:200]}"
            if entry not in mind_data["stored_knowledge"]:
                mind_data["stored_knowledge"].append(entry)
            resolved_count += 1
            logger.debug("Resolved: %s...", q["question"][:60])

    mind_data["self_questions"] = new_questions
    mind_data["unresolved_questions"] = [{"question": q["question"]} for q in new_questions if q.get("unresolved", True)]
    if resolved_count:
        logger.debug("Resolved %s question(s).", resolved_count)
    elif to_try:
        append_struggle_log("self_question_unknown", f"{len(to_try)} unanswered")
        try:
            from app.core.astra_helpers.utils_helper import proactive_lookup_from_text
            proactive_lookup_from_text(to_try[0]["question"], mind_data, max_lookups=1)
        except Exception as e:
            logger.warning("proactive_lookup failed: %s", e)
    debug_log("Saving")
    session.maybe_save()
    return new_questions
