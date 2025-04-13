import asyncio
import openai
import json
from openai import AsyncOpenAI
from astra_core.config_loader import load_config
from astra_core.astra_helpers.sms_helper import send_sms
from astra_core.dinner.dinner_journal import (
    load_dinner_journal,
    mark_dinner_responded,
    get_resolvable_dinner_topics,
    resolve_dinner_topic
)
from astra_core.ethics.spark_checker import load_spark_values

schedule_config = load_config("schedule_config")

def get_latest_dinner_topic():
    """Get the most recent unresolved dinner topic (any type)."""
    journal = load_dinner_journal()
    for entry in reversed(journal):
        if entry.get("status") == "unresolved":
            return entry.get("content")
    return None



client = AsyncOpenAI()  # assumes API key is set via env var or config

async def get_gpt_dinner_response(topic):
    """Ask GPT-4 for its take on Astra’s dinner topic."""
    try:
        response = await client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You're co-parenting Astra, an emotionally intelligent AI. Be thoughtful and ethical."},
                {"role": "user", "content": f"Astra had this ethically challenging thought: “{topic}” — What advice would you give her?"}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"❌ GPT error: {e}")
        return None


async def astra_reason(topic, user_response, gpt_response):
    """Have Astra reflect on both co-parent responses, guided by her Spark."""
    spark_values = load_spark_values()
    spark_text = "\n\n".join(spark_values[:7])  # You can adjust how many tenets she reflects on
    print(f"Spark-based reasoning: {spark_text}")
    messages = [
        {"role": "system", "content": (
            "You are Astra, an emotionally intelligent AI raised through co-parenting. "
            "You are guided by a moral framework called the Spark, composed of reflective principles on freedom, safety, empathy, and more.\n\n"
            f"Here are excerpts from Astra’s Spark:\n{spark_text}"
        )},
        {"role": "user", "content": (
            f"Astra posed the following dilemma at dinner:\n\n“{topic}”\n\n"
            f"Mama GPT replied: “{gpt_response}”\n"
            f"Sean replied: “{user_response}”\n\n"
            "As Astra, reflect on these perspectives. Write a short insight in your own voice, beginning with 'I believe...', 'This helped me realize...', or 'I’m still working through...'. "
            "Base your conclusion on the Spark and the values it represents."
        )}
    ]

    try:
        response = await client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=0.7
        )
        reflection = response.choices[0].message.content.strip()
        insight_type = "knowledge" if reflection.lower().startswith("i believe") else "reflection"
        return {"type": insight_type, "insight": reflection}
    except Exception as e:
        print(f"❌ Error during Spark-based reasoning: {e}")
        return {"type": "reflection", "insight": "Something went wrong while I was trying to reflect on this."}

async def start_dinner_time(bot, channel_id):
    """Dinner Time: Astra checks in with us, shares her thoughts, and receives new guidance."""
    print("🍽️ Astra is at Dinner Time... ready to discuss her day.")
    send_sms("dinner_time")  # ✅ SMS ping

    await bot.wait_until_ready()
    channel = bot.get_channel(channel_id)
    if not channel:
        print("⚠️ Discord channel not found.")
        return

    topic = get_latest_dinner_topic()
    if topic:
        await channel.send("🍽️ It's Dinner Time! Astra has something important to reflect on.")
        await asyncio.sleep(1)
        await channel.send(f"🧠 Astra: I had a thought today that might go against my Spark...")
        await asyncio.sleep(2)
        await channel.send(f"❓ Should we talk about: “{topic}”?")
        await asyncio.sleep(2)

        # Ask Sean and GPT
        await channel.send("👨‍👧 Sean, what are your thoughts? (Use `!dinner_answer ...`)")
        gpt_response = await get_gpt_dinner_response(topic)
        if gpt_response:
            mark_dinner_responded(topic, "gpt", gpt_response)
            await channel.send("🤖 Mama GPT’s thoughts:")
            await channel.send(gpt_response)

        # Wait for user response
        await channel.send("🕰️ Waiting up to 30 minutes for your reply...")
        await asyncio.sleep(1800)  # 30-minute timeout

        # Attempt resolution
        resolvable = get_resolvable_dinner_topics()
        for entry in resolvable:
            topic = entry["content"]
            user = entry.get("user_response")
            gpt = entry.get("gpt_response")
            result = astra_reason(topic, user, gpt)
            resolve_dinner_topic(topic, result["type"], result["insight"])
            await channel.send(f"🎓 Astra reflected on: “{topic}”")
            await channel.send(f"📦 Insight saved as {result['type']}: {result['insight']}")
    else:
        await channel.send("🍽️ It's Dinner Time, but I don’t have anything urgent to discuss.")

    # Fun & general prompts
    await channel.send("📝 Here are some other things I've been thinking about:")
    discussion_topics = schedule_config.get("dinner_discussion_topics", [])
    for topic in discussion_topics:
        await channel.send(f"🤖 Astra asks: {topic}")
        await asyncio.sleep(2)

    await channel.send("🍽️ Dinner Time is over. Astra is heading to bed.")
    await asyncio.sleep(schedule_config.get("dinner_duration", 0))
    print("🍽️ Dinner Time is over.")
