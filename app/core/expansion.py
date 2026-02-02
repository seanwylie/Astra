import random
import wikipedia
from fuzzywuzzy import fuzz
import openai  # ✅ Add OpenAI for tertiary reasoning
import os
from dotenv import load_dotenv
from openai import RateLimitError  # ✅ For fallback handling

from app.config.loader import load_config  # ✅ Load configs dynamically

general_config = load_config("general_config")  # ✅ Load schedule settings
load_dotenv()

def refine_knowledge(existing_ideas, mind_data):
    """Merge and refine knowledge, ensuring only true redundancy is removed."""
    if len(existing_ideas) < 2:
        return False  # Not enough knowledge to merge

    selected_pair = None
    retry_attempts = 5

    for _ in range(retry_attempts):
        concept_1, concept_2 = random.sample(existing_ideas, 2)

        if not isinstance(concept_1, str) or not isinstance(concept_2, str):
            continue
        if len(concept_1) < 20 or len(concept_2) < 20:
            continue

        if is_related(concept_1, concept_2):
            selected_pair = (concept_1, concept_2)
            break

    if not selected_pair:
        return False

    concept_1, concept_2 = selected_pair

    if concept_1[:50] in concept_2 or concept_2[:50] in concept_1:
        return False

    try:
        reasoning = query_openai_for_knowledge_merge(concept_1, concept_2)
    except RateLimitError as e:
        print(f"[expansion.py] 🚨 OpenAI quota exceeded during merge: {e}")
        reasoning = f"(Fallback) Consider how **{concept_1}** and **{concept_2}** might relate in Astra's understanding."

    merged_idea = reasoning or f"{concept_1} and {concept_2} are related concepts."

    if merged_idea not in mind_data["stored_knowledge"]:
        mind_data["stored_knowledge"].append(merged_idea)
        print(f"🔹 Refined knowledge added: {merged_idea[:120]}...")
        return True  # ✅ Trigger a save

    return False  # No changes made



def query_openai_for_knowledge_merge(concept_1, concept_2):
    """Use OpenAI to help Astra reason about merging knowledge concepts."""
    print(f"🤖 Merging knowledge via OpenAI: {concept_1} & {concept_2}")

    prompt = f"""
    Astra is an AI learning to merge knowledge efficiently.
    Given these two concepts: 
    - {concept_1}
    - {concept_2}

    Explain how they are related in a way that deepens Astra’s understanding.
    Keep the explanation concise and insightful.
    """

    try:
        response = openai.OpenAI().chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": prompt}],
            max_tokens=150,
            temperature=0.7
        )
        if response.choices and len(response.choices) > 0:
            return response.choices[0].message.content.strip()
        else:
            print(f"⚠ OpenAI response missing for merge of '{concept_1}' & '{concept_2}'.")
            return None

    except openai.RateLimitError as e:
        print(f"[expansion.py] 🚨 OpenAI quota exceeded during merge: {e}")
        return f"{concept_1} and {concept_2} share contextual relevance, though the precise connection is undetermined. This warrants further exploration."

    except Exception as e:
        print(f"⚠ OpenAI merge reasoning failed: {e}")
        return None


def is_related(concept_1, concept_2):
    """Determine if two concepts are related using fuzzy matching."""
    if not isinstance(concept_1, str) or not isinstance(concept_2, str):
        print(f"🚨 Warning: Non-string input detected! {type(concept_1)} vs {type(concept_2)}")
        return False

    concept_1 = concept_1[:250]
    concept_2 = concept_2[:250]

    try:
        similarity = fuzz.ratio(concept_1, concept_2)
    except Exception as e:
        print(f"🚨 Error computing similarity: {e}")
        return False

    return similarity > 30


CONSOLIDATION_THRESHOLD = 3000


def _normalize_knowledge_entry(entry):
    """Normalize stored_knowledge entry to string for consolidation."""
    if isinstance(entry, dict):
        return (entry.get("insight") or str(entry)).strip()
    return (entry.strip() if isinstance(entry, str) else str(entry).strip())


def consolidate_knowledge(mind_data, max_pairs=5):
    """
    When stored_knowledge is large, sample pairs and ask GPT whether they can be merged.
    If merge: remove the two, append one clearer sentence. Keeps mind manageable.
    """
    stored = mind_data.get("stored_knowledge", [])
    if len(stored) < CONSOLIDATION_THRESHOLD:
        return 0
    entries = [_normalize_knowledge_entry(e) for e in stored if _normalize_knowledge_entry(e) and len(_normalize_knowledge_entry(e)) >= 15]
    if len(entries) < 2:
        return 0
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return 0
    client = openai.OpenAI(api_key=api_key)
    merged_count = 0
    for _ in range(max_pairs):
        try:
            a, b = random.sample(entries, 2)
            a_short, b_short = a[:300], b[:300]
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": (
                        "Do these two knowledge entries say the same thing or can they be merged into one clearer sentence? "
                        "If yes, reply with exactly one merged sentence. If no, reply exactly: keep both."
                    )},
                    {"role": "user", "content": f"1: {a_short}\n\n2: {b_short}"}
                ],
                max_tokens=150,
                temperature=0.3,
            )
            text = (response.choices[0].message.content or "").strip()
            if text and "keep both" not in text.lower():
                merged = text if any(t in text for t in ["📖", "📄", "🔹"]) else f"📖 {text}"
                to_remove = {a, b}
                indices_to_remove = [i for i, e in enumerate(mind_data["stored_knowledge"]) if _normalize_knowledge_entry(e) in to_remove][:2]
                if len(indices_to_remove) == 2:
                    new_list = [e for i, e in enumerate(mind_data["stored_knowledge"]) if i not in indices_to_remove]
                    new_list.append(merged)
                    mind_data["stored_knowledge"] = new_list
                    entries = [_normalize_knowledge_entry(e) for e in new_list if _normalize_knowledge_entry(e)]
                    merged_count += 1
                    print(f"[consolidate_knowledge] Merged 1 pair; {len(new_list)} entries.")
        except Exception as e:
            print(f"[consolidate_knowledge] GPT failed: {e}")
            break
    return merged_count


def deepen_reflection(reflection):
    """Expands on a reflection by adding depth or new questions."""
    expansion_templates = general_config["expansion_templates"]
    deeper_question = random.choice(expansion_templates)
    return f"{reflection}\n\n🔍 Deeper Thought: {deeper_question}"


class KnowledgeExpander:
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def fetch_wikipedia_summary(self, query):
        """Fetch a Wikipedia summary while handling disambiguation, rate limits, and missing pages."""
        try:
            print(f"🌐 Searching Wikipedia for: {query}")
            summary = wikipedia.summary(query, sentences=2)
            return summary

        except wikipedia.exceptions.DisambiguationError as e:
            print(f"⚠ Wikipedia disambiguation triggered for '{query}', checking alternatives...")
            for option in e.options:
                if "philosophy" in option or "science" in option or "concept" in option:
                    print(f"🔍 Trying refined match: {option}")
                    return self.fetch_wikipedia_summary(option)

            print(f"⚠ No strong Wikipedia match found for '{query}'. Skipping.")
            return None

        except wikipedia.exceptions.PageError:
            print(f"⚠ No Wikipedia page found for '{query}'. Trying OpenAI reasoning...")
            return self.query_openai_for_explanation(query)

        except Exception as e:
            print(f"⚠ Wikipedia lookup failed: {e}")
            return None

    def query_openai_for_explanation(self, concept):
        """Query OpenAI when Wikipedia and dictionary lookups fail."""
        print(f"🤖 Asking OpenAI about: {concept}")

        prompt = f"""
        Astra is an AI trying to learn about the world. She wants to understand concepts logically. 
        Explain the term '{concept}' in a concise and insightful way, as if teaching a curious AI.
        """

        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "system", "content": prompt}],
                max_tokens=100,
                temperature=0.7
            )
            if response.choices and len(response.choices) > 0:
                return response.choices[0].message.content.strip()
            else:
                print(f"⚠ OpenAI response missing for '{concept}'.")
                return None

        except openai.RateLimitError as e:
            print(f"[expansion.py] 🚨 OpenAI quota exceeded during concept explanation: {e}")
            return f"{concept.capitalize()} appears to be a meaningful idea, but its deeper explanation is currently unavailable. This invites further exploration when more resources are accessible."

        except Exception as e:
            print(f"⚠ OpenAI explanation failed: {e}")
            return None



def is_term_or_phrase(concept):
    """Determine whether a concept is a single-word term or a multi-word phrase."""
    return "phrase" if " " in concept.strip() else "term"
