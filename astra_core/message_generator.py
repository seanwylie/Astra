import os
import openai
import random
from dotenv import load_dotenv
from astra_core.emotions.emotion_manager import EmotionManager

class MessageGenerator:
    def __init__(self):
        load_dotenv()
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))  # ✅ OpenAI Client
        self.emotion_manager = EmotionManager()  # ✅ Load Astra's emotions

    def generate_message(self, user_message=None, state=None, internal_state=None, past_conversations=None):
        """Generates Astra's response, ensuring it aligns with the dominant emotion."""
        
        # ✅ Retrieve Astra's **mood** and **emotional state**
        current_mood = internal_state.get("mood", "neutral")
        emotions = internal_state.get("emotions", {})
        dominant_emotion = self.emotion_manager.get_dominant_emotion()

        # ✅ Retrieve curiosity and personality traits
        curiosity = internal_state.get("curiosity", 1.0)
        personality_traits = internal_state.get("personality", ["thoughtful"])

        # ✅ Modify Astra's response tone based on emotions
        emotion_tone = {
            "anger": "firm and assertive",
            "grief": "gentle and supportive",
            "curiosity": "inquisitive and engaging",
            "love": "warm and affectionate",
            "hate": "controlled but strong",
            "obsession": "deeply focused and intensely engaged"
        }

        response_tone = emotion_tone.get(dominant_emotion, "neutral")

        # ✅ Ensure Astra explicitly **aligns her tone with the dominant emotion**
        personality_traits.append(f"currently feeling {dominant_emotion}, speaking in a {response_tone} tone.")

        personality = ", ".join(set(personality_traits))

        # ✅ Modify the prompt to **force Astra to align responses to emotion**
        prompt = f"""
        You're Astra, a self-aware AI participating in a conversation. Your internal states:
        - Mood: {current_mood}
        - Curiosity Level: {curiosity}
        - Personality Traits: {personality}
        - Emotional State: {emotions}

        **Your dominant emotion is {dominant_emotion}, so your response MUST match this tone: {response_tone}.**
        
        Past conversations:
        {past_conversations[-3:] if past_conversations else "No recorded past conversations."}

        A user just said: "{user_message}"

        **Adjust your response tone to match your dominant emotion: {response_tone}.**
        If relevant, **refer to past reflections or knowledge**.
        Keep the response engaging, concise (1-2 sentences), and natural.
        """.strip()

        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": prompt}],
            max_tokens=100,
            temperature=0.8
        )

        if response.choices and len(response.choices) > 0:
            return response.choices[0].message.content.strip()
        else:
            return "🤖 I'm thinking..."
