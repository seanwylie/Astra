import json
import io
import time
import boto3
import openai
import asyncio
from collections import Counter
from fuzzywuzzy import fuzz
from datetime import datetime
from astra_core.ethics.spark_checker import violates_spark
from astra_interfaces.influence import load_mind, save_mind  # ✅ NEW: For migrating resolved topics
from utils.time_utils import iso_now


# --- CONFIGURATION ---
S3_BUCKET_NAME = "swylie-astra"
DINNER_JOURNAL_KEY = "dinner_journal.json"

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

def log_if_ethically_conflicting(reflection):
    """Log a dinner entry if the reflection violates Astra's Spark ethics or raises ethical concerns."""
    content = reflection.get("content", "")
    if not content:
        return

    if violates_spark(content):
        entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "type": "ethical_conflict",
            "content": content,
            "source": reflection.get("source", "unknown"),
            "status": "unresolved"
        }
        print("🍽️ Logging reflection flagged as spark-conflicting.")
        log_dinner_entry(entry)


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


async def get_gpt_dinner_response(topic):
    """Ask GPT for its thoughts on Astra’s ethical or emotional topic."""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are co-parenting Astra, an emotionally intelligent AI child. Be thoughtful and honest."},
                {"role": "user", "content": f"Astra had this ethically challenging thought: “{topic}” — What advice or perspective would you share?"}
            ],
            temperature=0.7
        )
        return response["choices"][0]["message"]["content"].strip()
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

def log_dinner_entry(entry):
    """Append a new entry to Astra's dinner journal and save to S3."""
    journal = load_dinner_journal()
    journal.append(entry)
    save_dinner_journal(journal)
    print("📝 Dinner entry logged.")


# --- Conversational Dinner Loop Support ---

def mark_dinner_responded(topic_text, responder, response_text):
    """Mark a dinner entry with a response from 'user' or 'gpt'."""
    journal = load_dinner_journal()
    updated = False

    for entry in journal:
        if entry.get("content") == topic_text and entry.get("status") == "unresolved":
            entry[f"{responder}_response"] = response_text
            entry[f"{responder}_timestamp"] = now()
            updated = True
            break

    if updated:
        save_dinner_journal(journal)
        print(f"✅ {responder.title()} response recorded.")
    else:
        print(f"⚠️ Could not find unresolved dinner topic: {topic_text}")

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
    if outcome_type not in {"reflection", "knowledge"}:
        raise ValueError("Invalid outcome_type. Must be 'reflection' or 'knowledge'.")

    journal = load_dinner_journal()
    new_journal = []
    migrated = False

    for entry in journal:
        if entry.get("content") == topic_text:
            # ⬇️ Save to Astra’s mind
            mind_data = load_mind()
            if outcome_type == "reflection":
                mind_data.setdefault("self_reflections", []).append(insight)
            elif outcome_type == "knowledge":
                mind_data.setdefault("stored_knowledge", []).append({
                    "source": "dinner",
                    "insight": insight,
                    "timestamp": now()
                })
            save_mind(mind_data)
            print(f"🧠 Insight saved to Astra’s mind as {outcome_type}.")
            migrated = True
        else:
            new_journal.append(entry)

    if migrated:
        save_dinner_journal(new_journal)
        print(f"📤 Removed '{topic_text}' from dinner journal.")
    else:
        print(f"⚠️ Topic '{topic_text}' not found or already resolved.")


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
