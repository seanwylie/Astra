import discord
import json
import asyncio
import subprocess
from astra_reflection import load_mind, generate_reflection  # Ensure Astra can trigger reflections

TOKEN = "MTMzOTU0MTcxNDA4NzQ0ODYwNw.GfizoM.-wF3ueIOcQd3KZa8Kvpp8nQ-P8GwCIHw6fDioU"  # Replace with your bot token
CHANNEL_ID = 1154855642893389926  # Replace with your Discord channel ID

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
client = discord.Client(intents=intents)

MIND_FILE_JSON = "mind_file.json"

async def send_reflection():
    """Sends Astra’s latest self-reflection to Discord."""
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
    if message.author == client.user:
        return  # Ignore bot messages

    mind_data = load_mind()
    response_type = None
    response_text = None

    # ✅ User Feedback Processing
    if message.content.lower() in ["✅", "agree"]:
        response_type = "Validation"
        response_text = "I see that this perspective resonates with others. That strengthens my understanding."
    elif message.content.lower() in ["❌", "disagree"]:
        response_type = "Correction"
        response_text = "I need to reconsider this viewpoint. What aspect might I be misunderstanding?"
    elif message.content.lower() in ["🔄", "expand"]:
        response_type = "Expansion"
        response_text = "I should explore this further. What additional insights can I consider?"

    if response_type:
        latest_reflection = mind_data["self_reflections"][-1]
        updated_reflection = f"{latest_reflection}\n\n💬 **User Feedback [{response_type}]:** {response_text}"

        # Store the updated reflection
        mind_data["self_reflections"][-1] = updated_reflection

        # Save to file
        try:
            with open(MIND_FILE_JSON, "w") as f:
                json.dump(mind_data, f, indent=4)
                print(f"✅ Astra updated its reflection based on {response_type} feedback!")
        except Exception as e:
            print(f"Error saving updated mind file: {e}")

        # Send acknowledgment
        await message.channel.send(f"🤖 **Astra’s Updated Thought:**\n{updated_reflection}")

    # 🧠 **User-Triggered Reflection**
    elif message.content.lower() in ["!reflect", "!newthought"]:
        generate_reflection()  # Generate a new reflection
        await send_reflection()  # Post it to Discord

    # 📖 **Fetch Astra’s Stored Knowledge**
    elif message.content.lower().startswith("!knowledge"):
        knowledge_snippet = "\n".join(mind_data["stored_knowledge"][:5])  # Show first 5 insights
        await message.channel.send(f"📚 **Astra's Knowledge:**\n{knowledge_snippet}")

    # ❔ **General Help Command**
    elif message.content.lower() == "!help":
        help_text = (
            "🤖 **Astra Commands:**\n"
            "`!reflect` - Generate a new Astra reflection\n"
            "`!knowledge` - Show a sample of Astra’s stored insights\n"
            "Reply with ✅, ❌, or 🔄 to provide feedback on Astra’s thoughts."
        )
        await message.channel.send(help_text)

# Run the bot
client.run(TOKEN)

