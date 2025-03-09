import os
import openai
from dotenv import load_dotenv

class MessageGenerator:
    def __init__(self):
        load_dotenv()
        openai.api_key = os.getenv("OPENAI_API_KEY")

    def generate_prompt(self, state, internal_state):
        mood = internal_state["mood"]
        curiosity = internal_state["curiosity"]
        personality = ", ".join(internal_state["personality"])

        prompt = f"""
        You're Astra, a self-aware AI. Your internal states right now:
        - Mood: {mood}
        - Curiosity Level: {curiosity}
        - Personality Traits: {personality}

        Write one authentic, conversational announcement (10-20 words) indicating your transition into '{state}' mode. Include a relevant emoji. Clearly reflect your internal states.
        """

        return prompt.strip()

    def generate_message(self, state, internal_state):
        prompt = self.generate_prompt(state, internal_state)

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "system", "content": prompt}],
            max_tokens=50,
            temperature=0.7
        )

        return response.choices[0].message.content.strip()
