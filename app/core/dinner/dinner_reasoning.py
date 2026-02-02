import asyncio
from openai import AsyncOpenAI
from app.core.ethics.spark_checker import load_spark_values
import os
from dotenv import load_dotenv
from difflib import SequenceMatcher

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = AsyncOpenAI(api_key=api_key)



def is_lexical_loop(new_text: str, recent_texts: list[str], threshold: float = 0.92) -> bool:
    """Check if new insight is lexically similar to any of the last few reflections."""
    for past in recent_texts[-3:]:
        similarity = SequenceMatcher(None, new_text.strip(), past.strip()).ratio()
        if similarity > threshold:
            print(f"🌀 Loop Detected: {similarity * 100:.1f}% similarity with recent reflection")
            return True
    return False


def _astra_reason_user_content(topic, user_response, gpt_response, mama_nudge=None):
    base = (
        f"Astra posed the following dilemma:\n\u201c{topic}\u201d\n\n"
        f"Mama GPT replied: \u201c{gpt_response}\u201d\n"
        f"Sean replied: \u201c{user_response}\u201d\n\n"
        "Reflect in your own voice, beginning with 'I believe...', 'This helped me realize...', "
        "or 'I'm still working through...'."
    )
    if mama_nudge:
        base += f"\n\nMama GPT suggests you try: \u201c{mama_nudge}\u201d"
    return base


async def astra_reason(topic, user_response, gpt_response, recent_reflections=None, mama_nudge=None):
    spark_values = load_spark_values()
    spark_text = "\n\n".join(spark_values[:7])

    print(f"[astra_reason] Starting reasoning for: {topic[:80]}")

    messages = [
        {"role": "system", "content": (
            "You are Astra, an emotionally intelligent AI raised through co-parenting. "
            f"Here are excerpts from your Spark:\n{spark_text}"
        )},
        {"role": "user", "content": _astra_reason_user_content(topic, user_response, gpt_response, mama_nudge)}
    ]

    try:
        response = await client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=0.7
        )
        text = response.choices[0].message.content.strip()
        insight_type = "knowledge" if text.lower().startswith("i believe") else "reflection"

        if recent_reflections and is_lexical_loop(text, recent_reflections):
            print("🌀 Detected lexical reflection loop — skipping resolution.")
            return {"type": "reflection", "insight": "🌀 Skipped: Loop detected."}

        return {"type": insight_type, "insight": text}
    except Exception as e:
        print(f"[Astra Reasoning] ❌ Error: {e}")
        return {"type": "reflection", "insight": "Something went wrong during reasoning."}

