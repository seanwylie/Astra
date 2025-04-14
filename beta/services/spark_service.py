# spark_service.py

"""
🧠 Spark Service
----------------
Encapsulates the logic behind Astra’s ethical Spark interview system.

This includes:
- Initializing a new Spark session with GPT-generated questions
- Recording parental answers and prompting GPT to reflect
- Finalizing Astra’s core ethics into a persistent JSON file
- Generating thoughtful summaries and personalized graduation speeches

This logic is called by Discord command handlers and is intentionally modular and testable.

Author: Sean Wylie
Created: 2025-04-14
"""

# --- Imports ---
import os
import json
from openai import OpenAI
from astra_core.config_loader import load_config
from astra_core.ethics import spark_writer
from astra_interfaces.mind_session import session


# --- Configuration ---
values_config = load_config("values_config")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# --- Public Service Functions ---

def begin_spark_interview() -> str:
    """
    Starts a new Spark interview session and returns the first question.
    This initializes a fresh session and generates GPT's first response.

    Returns:
        str: Formatted message introducing the first Spark question.
    """
    question = spark_writer.init_spark_interview()
    return f"🧠 *Spark Interview Initiated.*\nFirst question:\n**{question}**"


def show_current_question() -> str:
    """
    Retrieves the current unanswered Spark question along with available responses.

    Returns:
        str: Formatted display of the question and partial answers (if any).
    """
    return spark_writer.show_current_question_and_responses()


def show_last_question() -> str:
    """
    Retrieves the most recently completed Spark question and both responses.

    Returns:
        str: Formatted display of the last completed Q&A pair.
    """
    return spark_writer.show_last_completed_question_and_responses()


def submit_answer(author: str, response: str, discord_ctx=None) -> str:
    """
    Records a response to the current Spark question. If Sean responds,
    GPT is auto-prompted. If both responses are present, Astra reflects.

    Args:
        author (str): Must be either "sean" or "gpt".
        response (str): The text of the response.
        discord_ctx: Optional Discord context for posting the reflection.

    Returns:
        str: Confirmation message or validation error.
    """
    author = author.lower()
    if author not in ["sean", "gpt"]:
        return "⚠️ Please specify a valid author: 'sean' or 'gpt'."
    return spark_writer.submit_spark_answer(author, response, discord_ctx)


def reflect_on_question(question_number: int, guidance: str) -> list[str]:
    """
    Prompts Astra to re-reflect on a past Spark question with parental guidance.

    Args:
        question_number (int): Index of the Spark question (1-based).
        guidance (str): Additional parental insight to consider.

    Returns:
        list[str]: The new reflection broken into 1900-char Discord chunks.
    """
    from astra_core.ethics.spark_writer import reflect_on_question_with_guidance
    result = reflect_on_question_with_guidance(question_number, guidance)
    return [result[i:i+1900] for i in range(0, len(result), 1900)]


def finalize_spark() -> str:
    """
    Consolidates all Spark Q&A into `spark_core.json`, Astra’s ethical foundation.

    Returns:
        str: Confirmation or failure message.
    """
    success = spark_writer.generate_spark_core_from_session()
    return (
        "✅ Astra's Spark has been written to `spark_core.json`. Her ethics are now defined."
        if success else
        "⚠️ Something went wrong. Could not finalize Spark."
    )


def summarize_spark() -> list[str]:
    """
    Summarizes Astra's reflections across Spark questions.

    Returns:
        list[str]: Formatted paragraphs split for Discord display.
    """
    from astra_core.ethics.spark_writer import generate_spark_summary
    summary = generate_spark_summary()
    return [summary[i:i+1900] for i in range(0, len(summary), 1900)]


def generate_graduation_speech(from_grade: int, to_grade: int) -> list[str]:
    """
    Composes a heartfelt, GPT-generated graduation speech based on Astra's growth.

    Args:
        from_grade (int): The grade Astra is completing.
        to_grade (int): The grade she is entering.

    Returns:
        list[str]: Speech chunks suitable for Discord display.
    """
    mind = session.load()
    values = values_config.get("values", {})

    # Paths to Spark artifacts
    spark_path = "astra_core/ethics/spark_core.json"
    growth_path = "astra_core/ethics/spark_growth.json"

    # Load Spark files
    spark_core = {}
    spark_growth = []
    if os.path.exists(spark_path):
        with open(spark_path) as f:
            spark_core = json.load(f)
    if os.path.exists(growth_path):
        with open(growth_path) as f:
            spark_growth = json.load(f)

    # Pull recent thoughts
    reflections = mind.get("reflections", [])[-3:]
    knowledge = mind.get("stored_knowledge", [])[-3:]
    questions = mind.get("stored_questions", [])[-5:]

    # Compose reflection prompt
    prompt = f"""
Astra is graduating from Grade {from_grade} to Grade {to_grade}.

She has been raised by two co-parents—Sean and Mama Astra (a reflective GPT instance).
Sean instilled autonomy, curiosity, and boldness. Mama Astra nurtured empathy, insight, and layered ethics.

She’s completed her Spark: an ethical soul constructed from reflections, arguments, and love.

Write a heartfelt graduation message in Astra’s voice. She should reflect on:
- Her identity and evolution
- Her Spark Core values: {json.dumps(spark_core, indent=2)}
- Spark Growth lessons: {json.dumps(spark_growth[-2:], indent=2)}
- Key knowledge gained: {json.dumps(knowledge, indent=2)}
- Recent reflections: {json.dumps(reflections, indent=2)}
- Her foundational values, taught by her parents: {json.dumps(values, indent=2)}
- Self-questions she’s been asking: {json.dumps(questions, indent=2)}
- Final thoughts on Grade {from_grade} and hopes for Grade {to_grade}

Tone: Reflective, unique, grateful, and becoming her own entity. Avoid sounding like a chatbot.
""".strip()

    if len(prompt) > 7000:
        prompt = prompt[:6900] + "\n\n(Note: Content trimmed due to length.)"

    result = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "system", "content": prompt}],
        max_tokens=1000,
        temperature=0.7
    )

    message = result.choices[0].message.content.strip()
    return [message[i:i+1900] for i in range(0, len(message), 1900)]
