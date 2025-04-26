import asyncio
import os
from openai import AsyncOpenAI

from dotenv import load_dotenv
load_dotenv(dotenv_path=".env", override=True)

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def test_gpt():
    print("🔧 Sending test message to GPT...")
    try:
        response = await client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say hello politely."}
            ],
            temperature=0.5
        )
        print("✅ GPT Response:", response.choices[0].message.content)
    except Exception as e:
        print(f"❌ GPT Test Failed: {type(e).__name__} - {e}")

asyncio.run(test_gpt())
