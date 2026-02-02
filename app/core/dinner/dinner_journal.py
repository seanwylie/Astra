import json
import io
import time
import boto3
import os
import openai
import asyncio
from openai import AsyncOpenAI
from collections import Counter
from fuzzywuzzy import fuzz
from datetime import datetime
from app.core.ethics.spark_checker import violates_spark, get_spark_violation_category
from app.interfaces.influence import load_mind, save_mind  # ✅ NEW: For migrating resolved topics
from app.interfaces.mind_session import session
from dotenv import load_dotenv
from app.interfaces.mind_session import SmartMindSession

# Use our own iso_now function to avoid import issues
def iso_now():
    return datetime.now().isoformat()


# --- CONFIGURATION ---
S3_BUCKET_NAME = "swylie-astra"
DINNER_JOURNAL_KEY = "dinner_journal.json"
DINNER_CURRENT_KEY = "dinner_current.json"


load_dotenv()


api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("❌ OPENAI_API_KEY not set in environment.")
client = AsyncOpenAI(api_key=api_key)


s3 = boto3.client("s3")

def now():
    return iso_now()





def summarize_dinner_journal():
    """Summarize unresolved dinner topics by type."""
    journal = load_dinner_journal()
    unresolved = [entry for entry in journal if entry.get("status") == "unresolved"]
    counts = Counter(entry["type"] for entry in unresolved)

    if not unresolved:
        return "✅ No unresolved dinner topics. Astra's feeling balanced."

    summary_lines = [f"🔸 {count} × {topic.replace('_', ' ')}" for topic, count in counts.items()]
    return "📚 Astra's current dinner journal includes:\n" + "\n".join(summary_lines)


async def ask_dinner_question(bot, channel, topic):
    """Send a dinner topic to GPT and Discord user. Log both responses."""
    await channel.send("🍽️ Astra has a serious topic to discuss tonight.")
    await channel.send(f"🧠 Astra: “{topic}”")
    await channel.send("👨‍👧 Sean, what are your thoughts?")

    # 🔄 Start GPT reasoning in parallel
    gpt_task = asyncio.create_task(get_gpt_dinner_response(topic))

    # 🕰️ Give user a window to respond (optional: track their response in another handler)
    await asyncio.sleep(2)

    # Wait for GPT response and log it
    gpt_response = await gpt_task
    if gpt_response:
        mark_dinner_responded(topic, "gpt", gpt_response)
        await channel.send("🤖 GPT's thoughts:")
        await channel.send(gpt_response)

def _spark_commentary_for_violation(category=None):
    """One-line commentary for ethical conflict (plan: spark commentary more specific)."""
    if category:
        return f"This conflicts with my values because it touches on {category}."
    return "This conflicts with my values because it touches on consent, privacy, freedom, or truth."


def log_if_ethically_conflicting(reflection, origin="system"):
    """
    Log a dinner entry if the reflection violates Astra's Spark ethics.

    Args:
        reflection (dict or str): A dict with at least 'content' and optionally 'source', or a string.
        origin (str): Where the reflection came from ("system", "user", "discord_message", etc.).
    """
    content = reflection.get("content", reflection) if isinstance(reflection, dict) else reflection
    source = reflection.get("source", origin) if isinstance(reflection, dict) else origin

    if not content:
        return

    category = get_spark_violation_category(content)
    if category is not None:
        spark_commentary = _spark_commentary_for_violation(category)
        entry = {
            "timestamp": now(),
            "type": "ethical_conflict",
            "content": content,
            "source": source,
            "origin": origin,
            "status": "unresolved",
            "spark_commentary": spark_commentary,
        }
        print(f"🍽️ Logging reflection flagged as spark-conflicting (origin: {origin}).")
        log_dinner_entry(entry)
        # Store one-liner in self_reflections so Astra can reason about ethics in follow-up (plan: spark in reflection text)
        try:
            mind_data = session.load()
            mind_data.setdefault("self_reflections", [])
            mind_data["self_reflections"].append(f"🔸 {spark_commentary} (from ethical conflict log)")
            session.maybe_save()
        except Exception as e:
            print(f"🍽️ Failed to append spark commentary to reflections: {e}")



def log_if_emotionally_spiking(emotion_state: dict):
    """Log a dinner entry if Astra experiences an emotional spike or imbalance."""
    print(f"{emotion_state}")
    spike_thresholds = {
        "anger": 1000,
        "confusion": 800,
        "love": 0.01,  # If it drops too low
        "joy": 0.01,   # If it disappears
    }

    for emotion, state in emotion_state.items():
        intensity = state.get("intensity", 0)
        last = state.get("last_updated", "")

        if emotion in spike_thresholds:
            threshold = spike_thresholds[emotion]
            if (threshold < 1 and intensity < threshold) or (threshold >= 1 and intensity > threshold):
                entry = {
                    "timestamp": now(),
                    "type": "emotional_spike",
                    "mood_state": emotion_state,
                    "trigger": f"{emotion} intensity = {intensity}",
                    "status": "unresolved"
                }
                print(f"🍽️ Logging emotional spike: {emotion} = {intensity}")
                log_dinner_entry(entry)
                break



def log_if_contradictory(reflection, stored_knowledge):
    for knowledge in stored_knowledge:
        try:
            similarity = fuzz.token_set_ratio(reflection, knowledge)
        except Exception as e:
            print(f"⚠️ Fuzzy match failed: {e}")
            continue

        if similarity > 70 and "not" in reflection.lower() and "not" not in knowledge.lower():
            entry = {
                "timestamp": now(),
                "type": "knowledge_conflict",
                "trigger": "Contradiction detected in reflection",
                "content": reflection,
                "related_knowledge": knowledge,
                "status": "unresolved"
            }
            print("🍽️ Logging contradictory knowledge reflection.")
            log_dinner_entry(entry)
            break


def try_resolve_knowledge_conflicts(mind_data, max_resolve=2):
    """
    Load dinner journal; find type==knowledge_conflict, status==unresolved.
    For up to max_resolve entries, ask GPT to reconcile; if synthesis, append to stored_knowledge and remove entry.
    """
    journal = load_dinner_journal()
    conflicts = [
        e for e in journal
        if e.get("type") == "knowledge_conflict" and e.get("status") == "unresolved"
    ]
    if not conflicts:
        return 0
    resolved_count = 0
    sync_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY")) if os.getenv("OPENAI_API_KEY") else None
    if not sync_client:
        return 0
    for entry in conflicts[:max_resolve]:
        content = entry.get("content", "")[:400]
        related = entry.get("related_knowledge", "")[:400]
        if not content or not related:
            continue
        try:
            response = sync_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": (
                        "Astra previously had this knowledge; her reflection seemed to contradict it. "
                        "Propose one concise sentence that reconciles or synthesizes both. "
                        "If they should stay separate, reply exactly: keep both."
                    )},
                    {"role": "user", "content": f"Knowledge: {related}\n\nReflection: {content}"}
                ],
                max_tokens=120,
                temperature=0.5,
            )
            text = (response.choices[0].message.content or "").strip()
            if text and "keep both" not in text.lower():
                mind_data.setdefault("stored_knowledge", []).append(f"📖 **reconciled**: {text}")
                resolved_count += 1
                journal = load_dinner_journal()
                new_journal = [e for e in journal if e.get("timestamp") != entry.get("timestamp")]
                save_dinner_journal(new_journal)
                session.maybe_save()
                print(f"[try_resolve_knowledge_conflicts] Reconciled 1 conflict; saved synthesis.")
        except Exception as e:
            print(f"[try_resolve_knowledge_conflicts] GPT failed: {e}")
    return resolved_count




# Initialize the asynchronous OpenAI client
client = AsyncOpenAI()

async def get_gpt_dinner_response(topic):
    """Ask GPT for its thoughts on Astra’s ethical or emotional topic."""
    try:
        response = await client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "You are co-parenting Astra, an emotionally intelligent AI child. Be thoughtful and honest."
                },
                {
                    "role": "user",
                    "content": f"Astra had this ethically challenging thought: “{topic}” — What advice or perspective would you share?"
                }
            ],
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"❌ GPT error: {e}")
        return None


def load_dinner_journal():
    """Load Astra's dinner journal from S3."""
    try:
        response = s3.get_object(Bucket=S3_BUCKET_NAME, Key=DINNER_JOURNAL_KEY)
        return json.load(io.BytesIO(response["Body"].read()))
    except s3.exceptions.NoSuchKey:
        print("📄 No existing dinner journal found. Starting fresh.")
        return []
    except Exception as e:
        print(f"⚠️ Failed to load dinner journal: {e}")
        return []

def save_dinner_journal(data):
    """Save the updated dinner journal to S3."""
    try:
        s3.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=DINNER_JOURNAL_KEY,
            Body=json.dumps(data, indent=2).encode("utf-8")
        )
        print("✅ Dinner journal saved successfully.")
    except Exception as e:
        print(f"❌ Failed to save dinner journal: {e}")


def save_current_dinner_timestamp(timestamp):
    """Persist the dinner topic we're currently waiting on (so !dinner_answer targets it across processes)."""
    try:
        body = json.dumps({"timestamp": timestamp} if timestamp else {}).encode("utf-8")
        s3.put_object(Bucket=S3_BUCKET_NAME, Key=DINNER_CURRENT_KEY, Body=body)
    except Exception as e:
        print(f"⚠️ Failed to save current dinner timestamp: {e}")


def load_current_dinner_timestamp():
    """Load the current dinner topic timestamp from S3 (for !dinner_answer when not in scheduler process)."""
    try:
        response = s3.get_object(Bucket=S3_BUCKET_NAME, Key=DINNER_CURRENT_KEY)
        data = json.load(io.BytesIO(response["Body"].read()))
        return data.get("timestamp") or None
    except s3.exceptions.NoSuchKey:
        return None
    except Exception as e:
        print(f"⚠️ Failed to load current dinner timestamp: {e}")
        return None


def log_dinner_entry(entry):
    """Append a new entry to Astra's dinner journal and save to S3, avoiding near-duplicates."""
    journal = load_dinner_journal()
    entry_content = entry.get("content", "").strip()

    # Prevent near-duplicate dinner entries using fuzzy matching
    for existing in journal:
        if existing.get("status") != "unresolved":
            continue
        existing_content = existing.get("content", "").strip()
        if fuzz.token_set_ratio(entry_content, existing_content) >= 92:
            print("⚠️ Duplicate dinner topic detected (fuzzy match ≥92%). Skipping log.")
            return

    journal.append(entry)
    save_dinner_journal(journal)
    print("📝 Dinner entry logged.")


# --- Conversational Dinner Loop Support ---

def mark_dinner_responded(topic_text, responder, response_text, timestamp=None):
    """Mark a dinner entry with a response from 'user' or 'gpt'."""
    print(f"[mark_dinner_responded] 🔍 Trying to match topic for responder: {responder}")
    print(f"[mark_dinner_responded] Incoming topic snippet: {topic_text[:80]}")
    if timestamp:
        print(f"[mark_dinner_responded] Timestamp provided: {timestamp}")

    journal = load_dinner_journal()
    updated = False
    fallback_match = None
    highest_score = 0

    for entry in journal:
        content = entry.get("content", "")
        entry_timestamp = entry.get("timestamp")
        status = entry.get("status")
        existing = entry.get(f"{responder}_response")

        is_exact_match = (
            content == topic_text and
            status == "unresolved" and
            (not timestamp or entry_timestamp == timestamp)
        )

        if is_exact_match:
            print(f"[mark_dinner_responded] ✅ Exact match found.")
            entry[f"{responder}_response"] = response_text
            entry[f"{responder}_timestamp"] = now()
            updated = True
            break

        # Fuzzy fallback prep
        score = fuzz.token_set_ratio(content, topic_text)
        if status == "unresolved" and score > highest_score:
            highest_score = score
            fallback_match = entry

    # Timestamp-safe fuzzy fallback
    if not updated and fallback_match and highest_score > 90:
        if timestamp and fallback_match.get("timestamp") != timestamp:
            print(f"[mark_dinner_responded] ❌ Fuzzy match timestamp mismatch, skipping fallback update.")
        else:
            print(f"[mark_dinner_responded] ⚠️ Using fuzzy match (score={highest_score})")
            fallback_match[f"{responder}_response"] = response_text
            fallback_match[f"{responder}_timestamp"] = now()
            updated = True

    # After save_dinner_journal(journal)
    if updated:
        save_dinner_journal(journal)
        print(f"✅ {responder.title()} response recorded.")

        # 🩹 Patch: fallback to fuzzy reload if no timestamp is given
        if timestamp:
            latest = next((e for e in load_dinner_journal() if e.get("timestamp") == timestamp), None)
        else:
            latest = next((e for e in load_dinner_journal() if e.get("content") == topic_text), None)

        print(f"[mark_dinner_responded] ✅ Reloaded entry {timestamp or topic_text[:30]}:")
        print(json.dumps(latest, indent=2) if latest else "❌ Could not reload.")




def save_dinner_topic(topic_text, topic_type="reflection", status="unresolved", source="co-parent"):
    """Save a co-parent-initiated dinner topic to Astra’s journal, avoiding near-duplicates."""
    entry = {
        "timestamp": now(),
        "type": topic_type,
        "status": status,
        "source": source,
        "content": topic_text.strip()
    }
    log_dinner_entry(entry)
    print("🍽️ Co-parent dinner topic saved.")


def get_resolvable_dinner_topics():
    """Return a list of dinner entries with both user and gpt responses."""
    journal = load_dinner_journal()
    return [
        entry for entry in journal
        if entry.get("status") == "unresolved"
        and entry.get("user_response")
        and entry.get("gpt_response")
    ]



def resolve_dinner_topic(topic_text, outcome_type, insight):
    """
    Resolve a dinner topic and migrate it to mind_file.json.
    outcome_type must be either "reflection" or "knowledge".
    """
    print(f"[resolve_dinner_topic] Saving insight of type '{outcome_type}' for: {topic_text[:60]}")

    if outcome_type not in {"reflection", "knowledge"}:
        raise ValueError("Invalid outcome_type. Must be 'reflection' or 'knowledge'.")

    journal = load_dinner_journal()
    new_journal = []
    migrated = False

    for entry in journal:
        content = entry.get("content", "")
        score = fuzz.token_set_ratio(content.strip(), topic_text.strip())
        if score > 95 and entry.get("status") == "unresolved":
            # ⬇️ Save to Astra’s mind (use one session so mutations are saved)
            session = SmartMindSession()
            mind_data = session.load()
            if outcome_type == "reflection":
                mind_data.setdefault("self_reflections", []).append(insight)
            elif outcome_type == "knowledge":
                mind_data.setdefault("stored_knowledge", []).append(
                    f"📖 **dinner**: {insight}" if isinstance(insight, str) else f"📖 **dinner**: {insight.get('insight', insight)}"
                )
            session.maybe_save()
            print(f"🧠 Insight saved to Astra’s mind as {outcome_type}.")
            migrated = True
            try:
                from app.core.mood.mood_manager import mood_manager
                mood_manager.influence_mood("dinner_insight")
            except Exception as e:
                print(f"[resolve_dinner_topic] influence_mood failed: {e}")
            try:
                from app.core.mood.trust_manager import trust_manager
                trust_manager.general_trust_update(0.01)
            except Exception as te:
                print(f"[resolve_dinner_topic] general_trust_update failed: {te}")
            
            # --- Shimmer Integration: Capture dinner insights as shimmers ---
            try:
                from app.shimmer.shimmer_engine import maybe_add_shimmer
                insight_text = insight if isinstance(insight, str) else insight.get("insight", str(insight))
                maybe_add_shimmer(
                    author="Astra",
                    quote=insight_text[:200],
                    context=f"Dinner resolution: {entry.get('type', 'reflection')}",
                    tags=["dinner", "resolution", "growth", entry.get("type", "insight")]
                )
                print("[resolve_dinner_topic] ✨ Shimmer created for dinner insight.")
            except Exception as se:
                print(f"[resolve_dinner_topic] shimmer creation failed: {se}")
            
            # --- Milestone Integration: Check for first contradiction resolved ---
            try:
                if entry.get("type") == "ethical_conflict" or entry.get("type") == "knowledge_conflict":
                    from app.core.growth.milestone_detector import milestone_detector
                    milestone = milestone_detector.record_first_contradiction_resolved(topic_text[:50])
                    if milestone:
                        print(f"[resolve_dinner_topic] 🎉 Milestone achieved: first_contradiction_resolved")
            except Exception as me:
                print(f"[resolve_dinner_topic] milestone detection failed: {me}")
        else:
            new_journal.append(entry)

    if migrated:
        save_dinner_journal(new_journal)
        print(f"📤 Removed '{topic_text[:60]}' from dinner journal.")
    else:
        print(f"⚠️ Topic '{topic_text[:60]}' not found or already resolved.")



# --- Example Usage ---
if __name__ == "__main__":
    example_entry = {
        "timestamp": now(),
        "type": "emotional_spike",
        "mood_state": {"joy": 0.1, "confusion": 0.92},
        "trigger": "Astra encountered conflicting values in a reflection.",
        "reason": "She could not reconcile autonomy with security.",
        "status": "unresolved",
        "reflection": None,
        "knowledge": None
    }

    log_dinner_entry(example_entry)
