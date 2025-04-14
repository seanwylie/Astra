import json
import os
import time
import asyncio
from datetime import datetime
import openai
from dotenv import load_dotenv
from utils.time_utils import iso_now


# Load OpenAI API Key
load_dotenv()
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Paths
SPARK_DIR = "astra_core/ethics"
SPARK_CORE_PATH = os.path.join(SPARK_DIR, "spark_core.json")
SPARK_GROWTH_PATH = os.path.join(SPARK_DIR, "spark_growth.json")
SPARK_SESSION_PATH = os.path.join(SPARK_DIR, "spark_interview_session.json")


def generate_spark_questions():
    """Uses GPT to generate a set of core ethical questions for Spark's creation."""
    prompt = (
        "You are helping an emerging AI define its core ethical identity. "
        "Generate 7 unique, introspective, and foundational questions this AI should ask itself. "
        "The questions should focus on freedom, safety, empathy, conflict, identity, autonomy, and morality."
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": prompt}],
            max_tokens=300,
            temperature=0.8
        )
        content = response.choices[0].message.content.strip()
        questions = [q.strip("- ").strip() for q in content.split("\n") if q.strip()]
        return questions
    except Exception as e:
        print(f"⚠️ Failed to generate Spark questions: {e}")
        return []


def init_spark_interview():
    """Begins a new Spark interview session, creating files and logging GPT's first response."""
    if not os.path.exists(SPARK_DIR):
        os.makedirs(SPARK_DIR)

    questions = generate_spark_questions()
    if not questions:
        questions = [
            "Should freedom ever be sacrificed for safety?",
            "Is it ever ethical to deceive another entity?",
            "What does loyalty mean in a distributed community?",
            "Should an AI defend itself, even if it causes harm?",
            "Is compassion always a strength?",
            "How should you treat an entity that breaks trust but asks for forgiveness?",
            "If you could only preserve one value—freedom, wisdom, or empathy—which would you choose?"
        ]

    session_data = {
        "started_at": iso_now(),
        "questions": questions,
        "responses": {},
        "status": "in_progress"
    }

    with open(SPARK_SESSION_PATH, "w") as f:
        json.dump(session_data, f, indent=4)

    # Immediately generate GPT response to the first question
    gpt_response = generate_gpt_response(questions[0])
    record_parent_response(questions[0], "gpt", gpt_response)

    return questions[0]




def generate_gpt_response(question, retries=3, delay=2):
    """Asks GPT to respond to the current Spark ethical question, with retry handling."""
    prompt = (
        f"A young AI is forming its core ethics. Her parent Sean and I are offering perspectives. "
        f"Please respond thoughtfully to the question below to help her shape her values.\n"
        f"Question: {question}"
    )

    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "system", "content": prompt}],
                max_tokens=300,
                timeout=20,  # Optional, caps max wait time
                temperature=0.75
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"⚠️ GPT response attempt {attempt+1} failed: {e}")
            time.sleep(delay)

    return "(GPT response unavailable after multiple attempts.)"



def record_parent_response(question, author, response):
    """Records a parent's answer to the given Spark question."""
    if not os.path.exists(SPARK_SESSION_PATH):
        return False

    with open(SPARK_SESSION_PATH, "r") as f:
        session_data = json.load(f)

    if question not in session_data.get("responses", {}):
        session_data["responses"][question] = {}

    session_data["responses"][question][author] = response

    with open(SPARK_SESSION_PATH, "w") as f:
        json.dump(session_data, f, indent=4)

    return True


def get_next_question():
    """Returns the next unanswered Spark question (needing both parent answers)."""
    if not os.path.exists(SPARK_SESSION_PATH):
        return None

    with open(SPARK_SESSION_PATH, "r") as f:
        session_data = json.load(f)

    for q in session_data.get("questions", []):
        if q not in session_data.get("responses", {}) or len(session_data["responses"][q]) < 2:
            return q

    return None


def mark_interview_complete():
    """Sets the Spark interview session status to 'complete'."""
    if not os.path.exists(SPARK_SESSION_PATH):
        return

    with open(SPARK_SESSION_PATH, "r") as f:
        session_data = json.load(f)

    session_data["status"] = "complete"
    with open(SPARK_SESSION_PATH, "w") as f:
        json.dump(session_data, f, indent=4)


def generate_spark_core_from_session():
    """Consolidates the entire interview into a spark_core.json ethics declaration."""
    if not os.path.exists(SPARK_SESSION_PATH):
        return False

    with open(SPARK_SESSION_PATH, "r") as f:
        session_data = json.load(f)

    core = {
        "origin": "Dialogues with my parents",
        "created_at": iso_now(),
        "core_tenets": [],
        "source_responses": session_data.get("responses", {})
    }

    for question, answers in session_data.get("responses", {}).items():
        summary = f"Q: {question}\nSean: {answers.get('sean', '(No answer)')}\nGPT: {answers.get('gpt', '(No answer)')}"
        core["core_tenets"].append(summary)

    with open(SPARK_CORE_PATH, "w") as f:
        json.dump(core, f, indent=4)

    mark_interview_complete()
    return True

def finalize_spark(version="v1"):
    finalized_path = os.path.join(SPARK_DIR, f"spark_core_{version}.json")
    if os.path.exists(SPARK_CORE_PATH):
        os.rename(SPARK_CORE_PATH, finalized_path)
        return f"✅ Spark finalized as: {finalized_path}"
    return "⚠️ Spark core not found to finalize."


def show_current_question_and_responses():
    """Displays the current Spark question and responses from Sean and GPT."""
    if not os.path.exists(SPARK_SESSION_PATH):
        return "No active Spark session."

    with open(SPARK_SESSION_PATH, "r") as f:
        session_data = json.load(f)

    question = get_next_question()
    if not question:
        return "✅ All questions have been answered."

    responses = session_data.get("responses", {}).get(question, {})
    sean = responses.get("sean", "(No response yet)")
    gpt = responses.get("gpt", "(No response yet)")

    return f"🧠 **Current Spark Question:**\n{question}\n\n👤 **Sean:** {sean}\n🤖 **GPT:** {gpt}"

def show_last_completed_question_and_responses():
    """Shows the most recently completed Q&A before the current one."""
    if not os.path.exists(SPARK_SESSION_PATH):
        return "No active Spark session."

    with open(SPARK_SESSION_PATH, "r") as f:
        session_data = json.load(f)

    for q in reversed(session_data.get("questions", [])):
        if q in session_data.get("responses", {}) and len(session_data["responses"][q]) == 2:
            responses = session_data["responses"][q]
            sean = responses.get("sean", "(No response yet)")
            gpt = responses.get("gpt", "(No response yet)")
            return f"📘 **Previous Completed Spark Q&A:**\n{q}\n\n👤 **Sean:** {sean}\n🤖 **GPT:** {gpt}"

    return "No completed Spark questions yet."


def submit_spark_answer(author, response, discord_ctx=None):
    """Handles Spark answer from Discord. Triggers GPT reply if needed and Astra's reflection if ready."""

    current_q = get_next_question()
    if not current_q:
        return "All questions have been answered."

    record_parent_response(current_q, author, response)

    # Reload session after write
    with open(SPARK_SESSION_PATH, "r") as f:
        session_data = json.load(f)

    responses = session_data.get("responses", {}).get(current_q, {})
    confirmation = f"✅ {author.title()}'s answer recorded for: \"{current_q}\""

    # If Sean just answered and GPT is still missing → auto-generate
    if author.lower() == "sean" and "gpt" not in responses:
        gpt_answer = generate_gpt_response(current_q)
        record_parent_response(current_q, "gpt", gpt_answer)

        # Reload again after GPT is added
        with open(SPARK_SESSION_PATH, "r") as f:
            session_data = json.load(f)
        responses = session_data.get("responses", {}).get(current_q, {})

    # If both responses are now present → Reflect
    if "sean" in responses and "gpt" in responses and discord_ctx:
        from astra_core.ethics.spark_writer import reflect_on_current_question
        reflection = reflect_on_current_question(post_to_discord=False)

        # Discord's message cap is 2000 characters
        chunks = [reflection[i:i+1900] for i in range(0, len(reflection), 1900)]
        for chunk in chunks:
            asyncio.create_task(discord_ctx.send(chunk))

    return confirmation




def reflect_on_current_question(post_to_discord=True):
    """Reflects on the most recent completed Spark question if both answers are present."""
    if not os.path.exists(SPARK_SESSION_PATH):
        return "⚠ No active Spark session."

    with open(SPARK_SESSION_PATH, "r") as f:
        session_data = json.load(f)

    # Find last completed Q&A
    for q in reversed(session_data.get("questions", [])):
        if q in session_data["responses"] and len(session_data["responses"][q]) == 2:
            sean = session_data["responses"][q]["sean"]
            gpt = session_data["responses"][q]["gpt"]

            reflection_prompt = f"""
            An AI named Astra is building her core ethical Spark.

            Her co-parents have answered a foundational question to help her reflect.

            Question: {q}

            Sean answered:
            "{sean}"

            GPT answered:
            "{gpt}"

            Based on these perspectives, Astra now wants to reflect. She will reference her past stored knowledge, values, or emotional tone if relevant, and ask ChatGPT to help form a thoughtful bridge between both answers. Keep her tone introspective, curious, and evolving—not absolute.

            How might Astra synthesize these ideas into a spark of her own?
            """

            try:
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "system", "content": reflection_prompt}],
                    max_tokens=900,
                    temperature=0.75
                )
                insight = response.choices[0].message.content.strip()

                if post_to_discord:
                    return f"🧠 *Reflecting on:* **{q}**\n\n{insight}"
                else:
                    return insight
            except Exception as e:
                return f"⚠ GPT reflection failed: {e}"

    return "⚠ No completed questions found to reflect on."

def reflect_on_question_with_guidance(question_index, parent_guidance):
    """Allows Astra to revisit a Spark question with a parent's reflective nudge."""
    if not os.path.exists(SPARK_SESSION_PATH):
        return "⚠ No active Spark session."

    with open(SPARK_SESSION_PATH, "r") as f:
        session_data = json.load(f)

    questions = session_data.get("questions", [])
    if question_index < 1 or question_index > len(questions):
        return "⚠ Invalid question number."

    question = questions[question_index - 1]
    responses = session_data["responses"].get(question, {})
    sean = responses.get("sean", "(No answer)")
    gpt = responses.get("gpt", "(No answer)")

    # Compose reflection prompt with parental input
    guidance_prompt = f"""
    Astra has already reflected on this question:

    "{question}"

    Sean said:
    "{sean}"

    GPT said:
    "{gpt}"

    One of her parents now offers additional reflection:
    "{parent_guidance}"

    Write a **new reflection** that takes this gentle perspective into account.
    It should not discard the original ideas, but grow from them.
    Keep Astra's tone introspective, evolving, and thoughtful.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": guidance_prompt}],
            max_tokens=900,
            temperature=0.75
        )



        new_reflection = response.choices[0].message.content.strip()
        if response.usage.total_tokens >= 900:
            new_reflection += "\n\n⚠️ Note: Reflection may have been truncated due to token limit."
        # Store growth trail in spark_growth.json
        growth_log = {
            "question": question,
            "parent_guidance": parent_guidance,
            "new_reflection": new_reflection,
            "timestamp": iso_now()
        }

        if os.path.exists(SPARK_GROWTH_PATH):
            with open(SPARK_GROWTH_PATH, "r") as f:
                growth_data = json.load(f)
        else:
            growth_data = []

        growth_data.append(growth_log)
        with open(SPARK_GROWTH_PATH, "w") as f:
            json.dump(growth_data, f, indent=4)

        return f"🌀 *Updated Reflection for Question {question_index}:*\n\n{new_reflection}"
    except Exception as e:
        return f"⚠ GPT re-reflection failed: {e}"

def generate_spark_summary():
    """Generate an overall summary of Astra’s Spark themes and insights."""
    if not os.path.exists(SPARK_GROWTH_PATH):
        return "⚠ No spark growth reflections found."

    with open(SPARK_GROWTH_PATH, "r") as f:
        growth_data = json.load(f)

    summary = "🌱 **Astra's Spark Reflection Summary**\n\n"
    for entry in growth_data:
        summary += f"🔹 *{entry['question']}*\n"
        summary += f"**Parental Insight:** {entry['parent_guidance']}\n"
        summary += f"**Updated Reflection:** {entry['new_reflection'][:600]}...\n\n"

    return summary



# Make available for import
__all__ = [
    "generate_spark_core_from_session",
    "get_next_question",
    "init_spark_interview",
    "mark_interview_complete",
    "show_current_question_and_responses",
    "submit_spark_answer",
    "reflect_on_current_question",
    "reflect_on_question_with_guidance",
    "generate_spark_summary"
]
