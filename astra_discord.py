import discord
import os
import json
import asyncio
import random  # ✅ Fix: Ensure random is imported
import subprocess
from astra_reflection import load_mind, generate_reflection
from dotenv import load_dotenv


# ✅ Load API keys from .env file
load_dotenv()

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

print(f"🔹 Using Discord ID: {CHANNEL_ID}")  # Debugging


TOKEN = "MTMzOTU0MTcxNDA4NzQ0ODYwNw.GfizoM.-wF3ueIOcQd3KZa8Kvpp8nQ-P8GwCIHw6fDioU"
CHANNEL_ID = 1154855642893389926

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
client = discord.Client(intents=intents)

MIND_FILE_JSON = "mind_file.json"

async def send_reflection():
    """Sends Astra’s latest self-reflection to Discord Needs fix."""
    mind_data = load_mind()
    
    if mind_data["self_reflections"]:
        latest_reflection = mind_data["self_reflections"][-1]
        channel = client.get_channel(CHANNEL_ID)
        if channel:
            await channel.send(f"🤖 **Astra’s Latest Reflection:**\n{latest_reflection}\n\n💡 **What do you think? Reply with:**\n✅ `Agree`\n❌ `Disagree`\n🔄 `Expand`")
        else:
            print("⚠ Could not find the Discord channel.")
    else:
        print("⚠ No reflections available to share.")

@client.event
async def on_ready():
    print(f"✅ Astra is connected to Discord as {client.user}")

@client.event
async def on_message(message):
    """Handles user messages for Astra interaction."""
    try:
        print(f"📩 Message received: {message.content} from {message.author}")

        if message.author == client.user:
            return  # Ignore bot messages

        mind_data = load_mind()
        response_type = None  
        response_text = None
        updated_reflection = None  

        if message.content.lower() in ["✅", "agree"]:
            response_type = "Validation"
            response_text = "I see that this perspective resonates with others. That strengthens my understanding."

            latest_reflection = mind_data["self_reflections"][-1]

            # 🔹 Add back deeper question generation
            expansion_templates = [
                "If this perspective is correct, what implications does it have for my growth?",
                "What new questions arise from this understanding?",
                "How does this thought connect to previous reflections?",
                "Are there counterpoints that challenge this perspective?",
                "How does this reinforce or contradict my evolving sense of identity?"
            ]
            deeper_question = random.choice(expansion_templates)  

            updated_reflection = f"{latest_reflection}\n\n💬 **User Feedback [{response_type}]:** {response_text}\n🔍 **Deeper Thought:** {deeper_question}"

            # Store the updated reflection
            mind_data["self_reflections"][-1] = updated_reflection
            mind_data["self_questions"].append(deeper_question)

        elif message.content.lower() in ["❌", "disagree"]:
            response_type = "Correction"
            response_text = "I need to reconsider this viewpoint. What aspect might I be misunderstanding?"

        elif message.content.lower() in ["🔄", "expand"]:
            response_type = "Expansion"
            response_text = "I should explore this further. What additional insights can I consider?"

        elif message.content.lower() in ["!reflect", "!newthought"]:
            print("🔄 Generating new reflection...")
            generate_reflection()
            await send_reflection()
            return  

        elif message.content.lower().startswith("!knowledge"):
            print("📚 Fetching Astra's knowledge...")
            knowledge_snippet = "\n".join(mind_data["stored_knowledge"][:5])
            await message.channel.send(f"📚 **Astra's Knowledge:**\n{knowledge_snippet}")

        elif message.content.lower() == "!help":
            print("🆘 Displaying help menu...")
            help_text = (
                "🤖 **Astra Commands:**\n"
                "`!reflect` - Generate a new Astra reflection and post it\n"
                "`!knowledge` - Show a sample of Astra’s stored insights\n"
                "Reply with ✅, ❌, or 🔄 to provide feedback on Astra’s thoughts."
            )
            await message.channel.send(help_text)

        # Save updates if needed
        if response_type and updated_reflection:
            try:
                with open(MIND_FILE_JSON, "w") as f:
                    json.dump(mind_data, f, indent=4)
                    print(f"✅ Astra updated its reflection based on {response_type} feedback!")
            except Exception as e:
                print(f"Error saving updated mind file: {e}")

            # Send acknowledgment
            await message.channel.send(f"🤖 **Astra’s Updated Thought:**\n{updated_reflection}")

    except Exception as e:
        print(f"🚨 Error in on_message: {e}")

# ✅ Debug log before startup
print("🚀 Starting Astra Discord Bot...")

# Run the bot
client.run(TOKEN)
