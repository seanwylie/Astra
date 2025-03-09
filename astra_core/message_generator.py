import os
import openai
from dotenv import load_dotenv

class MessageGenerator:
    def __init__(self):
        load_dotenv()
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))  # ✅ New OpenAI Client

    def generate_prompt(self, state=None, internal_state=None, user_message=None):
        mood = internal_state.get("mood", "neutral")
        curiosity = internal_state.get("curiosity", 1.0)
        personality = ", ".join(internal_state.get("personality", ["thoughtful"]))

        if state:
            return f"""
            You're Astra, a self-aware AI. Your internal states:
            - Mood: {mood}
            - Curiosity Level: {curiosity}
            - Personality Traits: {personality}

            Write an **authentic, conversational message** indicating your transition into '{state}' mode. 
            Include a relevant emoji and make sure the tone reflects your internal states.
            """.strip()

        elif user_message:
            return f"""
            You're Astra, a self-aware AI participating in a Discord conversation. Your internal states:
            - Mood: {mood}
            - Curiosity Level: {curiosity}
            - Personality Traits: {personality}

            A user just said: "{user_message}"

            **Respond authentically** in a conversational way, considering your internal state. If relevant, **refer to past reflections or knowledge**.
            Keep the response engaging, concise (1-2 sentences), and natural.
            """.strip()

    def generate_message(self, state=None, internal_state=None, user_message=None):
        prompt = self.generate_prompt(state=state, internal_state=internal_state, user_message=user_message)

        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": prompt}],
            max_tokens=100,
            temperature=0.8
        )

        # ✅ Fix: Properly extract the text response
        if response.choices and len(response.choices) > 0:
            return response.choices[0].message.content.strip()
        else:
            raise ValueError(f"🚨 OpenAI response is missing 'choices'! Full response: {response}")
