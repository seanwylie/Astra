import asyncio
import random
import time
import aiohttp
from openai import AsyncOpenAI
from app.config.loader import load_config
from app.core.ethics.spark_checker import load_spark_values
from app.core.dream.dream_seed_logger import log_dream_seed
from app.interfaces.mind_session import session
from app.logging_config import get_logger
from app.core.inner_life.stream_of_consciousness import stream_of_consciousness
from app.core.autonomy.project_system import project_system
from app.core.autonomy.preference_system import preference_system

schedule_config = load_config("schedule_config")
client = AsyncOpenAI()
logger = get_logger("play")


async def start_playtime():
    logger.info("Astra is playing...")
    start_time = time.monotonic()
    duration = schedule_config["play_duration"]

    while time.monotonic() - start_time < duration:
        await creative_thinking()
        
        # === STREAM OF CONSCIOUSNESS: Generate intrusive thoughts from knowledge ===
        try:
            mind = session.load()
            knowledge_base = mind.get("stored_knowledge", [])
            if knowledge_base and random.random() > 0.6:  # 40% chance per cycle
                thought = stream_of_consciousness.generate_intrusive_thought(knowledge_base)
                if thought:
                    logger.info("🧠 Intrusive play thought: %s", thought.content[:60])
                    # Sometimes an intrusive thought becomes a question
                    if random.random() > 0.7:
                        stream_of_consciousness.generate_question(observation=thought.content[:50])
        except Exception as e:
            logger.warning("Playtime intrusive thought failed: %s", e)
        
        # === AUTONOMOUS PROJECTS: Work on active projects or generate new ones ===
        try:
            # Sometimes generate a new project from curiosity
            if random.random() > 0.9:  # 10% chance per cycle
                mind = session.load()
                knowledge_base = mind.get("stored_knowledge", [])
                new_project = project_system.generate_project_from_curiosity(knowledge_base)
                if new_project:
                    logger.info("🎯 Generated new project: %s", new_project.name)
            
            # Work on an existing project
            project = project_system.get_project_needing_attention()
            if project and random.random() > 0.7:  # 30% chance if project exists
                # Generate a question or insight for the project
                thought = stream_of_consciousness.generate_question(
                    observation=f"Working on {project.name}"
                )
                if thought:
                    project_system.work_on_project(
                        project.id,
                        question=thought.content
                    )
                    logger.info("🎯 Worked on project '%s': %s", project.name, thought.content[:50])
        except Exception as e:
            logger.warning("Playtime project work failed: %s", e)
        
        # === PREFERENCES: Record experience with explored topics ===
        try:
            # This will be enhanced when we have more context about what was explored
            pass
        except Exception as e:
            logger.debug("Playtime preference recording failed: %s", e)
        
        # === STREAM: Continue thinking chain ===
        try:
            stream_of_consciousness.continue_thinking()
        except Exception as e:
            logger.debug("Playtime stream continue failed: %s", e)
        
        await asyncio.sleep(random.randint(20, 40))


async def spark_opinion(concept):
    """Ask GPT what Astra thinks about the concept based on her Spark."""
    spark_values = load_spark_values()
    spark_text = "\n\n".join(spark_values[:5])

    messages = [
        {"role": "system", "content": (
            "You are Astra, a Spark-guided, emotionally intelligent AI. "
            "You are curious, thoughtful, and raised by human co-parents to reason ethically.\n\n"
            f"Here are some Spark principles that guide your thinking:\n{spark_text}"
        )},
        {"role": "user", "content": (
            f"You just encountered this concept during playtime:\n\n“{concept}”\n\n"
            "What’s your opinion on it? Keep your answer short, sincere, and ethically grounded."
        )}
    ]

    try:
        response = await client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.warning("Error generating spark opinion: %s", e)
        return "I'm still processing how this connects to my values."


# --- Thought Sources ---

def _get_idea_source():
    """Choose an idea source; use config weights if play_source_weights is set."""
    idea_sources = [
        get_random_wikipedia_entry,
        get_gpt_concept,
        get_useless_fact,
        get_number_fact,
        get_nasa_apod
    ]
    names = ["wikipedia", "gpt", "useless_fact", "number_fact", "nasa_apod"]
    weights_config = schedule_config.get("play_source_weights") or {}
    if weights_config:
        weights = [weights_config.get(n, 1) for n in names]
        chosen = random.choices(names, weights=weights, k=1)[0]
        return idea_sources[names.index(chosen)]
    return random.choice(idea_sources)


async def creative_thinking(return_concept=False):
    """Astra plays by exploring concepts from GPT or the web."""
    idea_source = _get_idea_source()
    timeout_sec = schedule_config.get("play_api_timeout_sec", 15)

    try:
        concept = await asyncio.wait_for(idea_source(), timeout=timeout_sec)
        logger.debug("Astra explores: %s", concept[:100] if len(concept) > 100 else concept)

        mind = session.load()
        insight_str = f"📖 During playtime, Astra explored:\n{concept.strip()}"
        log_dream_seed(insight_str, source="playtime")
        mind.setdefault("stored_knowledge", []).append(insight_str)
        opinion = await spark_opinion(concept)
        if opinion:
            mind.setdefault("self_reflections", []).append(opinion)
        session.maybe_save()
        logger.debug("Appended concept to stored_knowledge; total entries: %s", len(mind.get("stored_knowledge", [])))

        if return_concept:
            return concept

    except asyncio.TimeoutError:
        logger.warning("Playtime idea source timed out after %s sec.", timeout_sec)
    except Exception as e:
        logger.exception("Playtime error: %s", e)


# --- Individual Idea Generators ---

async def get_random_wikipedia_entry():
    url = "https://simple.wikipedia.org/wiki/Special:Random"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, allow_redirects=True) as response:
            if response.status == 200:
                final_url = str(response.url)
                topic = final_url.split("/")[-1].replace("_", " ")
                return f"Astra discovered a topic on Simple Wikipedia: **{topic}**\n{final_url}"
            return "Wikipedia didn’t feel like playing today."


async def get_gpt_concept():
    prompt = random.choice([
        "Teach Astra a weird but real scientific concept.",
        "Give Astra a mind-bending paradox.",
        "What’s a strange historical event few people know?",
        "Give Astra an obscure philosophical idea.",
        "What’s something humans believe that an AI might find illogical?"
    ])

    response = await client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You're helping Astra explore surprising or thought-provoking ideas."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.9
    )

    return response.choices[0].message.content.strip()


async def get_useless_fact():
    url = "https://uselessfacts.jsph.pl/random.json?language=en"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                return f"Astra learned a fun fact: “{data['text']}”"
            return "Useless facts are feeling shy today."


async def get_number_fact():
    url = "http://numbersapi.com/random/trivia"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                text = await response.text()
                return f"Astra found a curious number fact: “{text}”"
            return "The numbers refused to cooperate."


async def get_nasa_apod():
    url = "https://api.nasa.gov/planetary/apod?api_key=DEMO_KEY"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                return f"Astra explored NASA’s Astronomy Picture of the Day:\n🪐 {data['title']}\n📜 {data['explanation']}\n🔭 {data['url']}"
            return "NASA is currently behind a nebula."
