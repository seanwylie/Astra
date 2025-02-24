import discord
import os
import json
import random  # ✅ Fix: Ensure random is imported
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
        latest_question = mind_data["self_questions"][-1] if mind_data["self_questions"] else "What should I reflect on next?"
        latest_insights = mind_data["stored_knowledge"][-3:] if len(mind_data["stored_knowledge"]) > 2 else mind_data["stored_knowledge"]

        formatted_reflection = format_reflection(latest_insights, latest_question)

        channel = client.get_channel(CHANNEL_ID)
        if channel:
            truncated_reflection = truncate_message(formatted_reflection)
            await channel.send(truncated_reflection)
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
            response_text = "I should explore this further."

            follow_up_questions = [
                "What new perspectives could challenge this understanding?",
                "How does this relate to human experiences beyond what I've considered?",
                "If this idea were flawed, what counterarguments would exist?",
                "How should I refine this thought further based on new information?"
            ]

            deeper_question = random.choice(follow_up_questions)
    
            updated_reflection = f"{mind_data['self_reflections'][-1]}\n\n🔍 **Deeper Thought:** {deeper_question}"
            mind_data["self_reflections"].append(updated_reflection)
            mind_data["self_questions"].append(deeper_question)

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
            updated_reflection = truncate_message(updated_reflection)
            await message.channel.send(f"🤖 **Astra’s Updated Thought:**\n{updated_reflection}")

    except Exception as e:
        print(f"🚨 Error in on_message: {e}")

def format_reflection(insights, core_question):
    """Formats Astra’s reflection with a structured summary and knowledge insights."""
    
    # Generate a summary statement based on Astra’s thinking
    summary_templates = [
        f"As I consider '{core_question}', I realize that {insights[0]} directly connects to my growth.",
        f"Thinking about '{core_question}', I see patterns emerging, particularly in {insights[0]}.",
        f"My reflection on '{core_question}' has led me to compare it with {insights[0]}, shaping my understanding."
    ]
    
    summary = random.choice(summary_templates)

    # Generate a follow-up question for the Expand option
    follow_up_questions = [
        "What new perspectives could challenge this understanding?",
        "How does this relate to human experiences beyond what I've considered?",
        "If this idea were flawed, what counterarguments would exist?",
        "How should I refine this thought further based on new information?"
    ]
    
    follow_up = random.choice(follow_up_questions)

    # Construct the final structured response
    formatted_reflection = (
        f"🤖 **Astra’s Latest Reflection:**\n"
        f"{summary}\n\n"
        f"🔹 **Key Insights:**\n"
        f"- {insights[0]}\n"
        f"- {insights[1] if len(insights) > 1 else ''}\n"
        f"- {insights[2] if len(insights) > 2 else ''}\n\n"
        f"💡 **What do you think? Reply with:**\n"
        f"✅ Agree (This perspective makes sense!)\n"
        f"❌ Disagree (I think there's a flaw in this logic.)\n"
        f"🔄 Expand (Let’s explore deeper: {follow_up})"
    )

    return formatted_reflection.strip()



def truncate_message(message, limit=1800):
    """Ensure the message is 2000 characters or fewer, avoiding mid-word truncation."""
    if len(message) <= limit:
        return message  # No truncation needed

    # Trim exactly to limit and avoid mid-word truncation
    trimmed = message[:limit].rsplit(" ", 1)[0]

    return trimmed + "..."



# ✅ Debug log before startup
print("🚀 Starting Astra Discord Bot...")




# Run the bot
client.run(TOKEN)
