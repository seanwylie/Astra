import json
import random
import time
import wikipedia

MIND_FILE_JSON = "mind_file.json"
MIND_FILE_ORIG = "mind_file_sean.json"

def load_mind():
    """Loads Astra's stored reflections and knowledge."""
    try:
        with open(MIND_FILE_JSON, "r") as f:
            mind_data = json.load(f)
    except FileNotFoundError:
        mind_data = {"self_reflections": [], "self_questions": [], "stored_knowledge": []}

    # Merge structured knowledge from mind_file_sean.json
    try:
        with open(MIND_FILE_ORIG, "r") as f:
            structured_data = json.load(f)
            if "insights" in structured_data:
                structured_knowledge = {entry["insight"] for entry in structured_data["insights"]}
                current_knowledge = set(mind_data["stored_knowledge"])  # Convert to a set to avoid duplicates

                # Merge new knowledge
                updated_knowledge = current_knowledge.union(structured_knowledge)
                mind_data["stored_knowledge"] = list(updated_knowledge)  # Convert back to a list

                print("🔹 Merging complete! Final stored knowledge count:", len(mind_data["stored_knowledge"]))
    except Exception as e:
        print(f"Error loading structured mind file: {e}")

    # 🔥 **Ensure we save the updated mind file**
    try:
        with open(MIND_FILE_JSON, "w") as f:
            json.dump(mind_data, f, indent=4)
            print("✅ Mind file successfully updated and saved!")
    except Exception as e:
        print(f"Error saving updated mind file: {e}")

    return mind_data

def save_mind(data):
    """Saves Astra's evolving mind file, ensuring uniqueness."""
    data["self_reflections"] = list(set(data["self_reflections"]))
    data["stored_knowledge"] = list(set(data["stored_knowledge"]))
    data["self_questions"] = list({q: q for q in data["self_questions"]}.values())  # Ensure uniqueness

    with open(MIND_FILE_JSON, "w") as f:
        json.dump(data, f, indent=4)

def fetch_wikipedia_summary(query):
    """Fetches a short summary from Wikipedia for a given query."""
    try:
        summary = wikipedia.summary(query, sentences=2)
        print(f"🌍 Wikipedia Lookup: {query}\n{summary}")
        return summary
    except wikipedia.exceptions.DisambiguationError as e:
        print(f"⚠ Wikipedia Disambiguation: {query} - {e.options}")
        return f"Multiple results found for {query}. Try a more specific request."
    except wikipedia.exceptions.PageError:
        print(f"⚠ Wikipedia Page Not Found: {query}")
        return f"No Wikipedia page found for {query}."
    except Exception as e:
        print(f"⚠ Wikipedia Fetch Error: {e}")
        return "An error occurred while retrieving Wikipedia data."

def generate_reflection():
    """Generates a new structured self-reflection."""
    mind_data = load_mind()

    # Step 1: Select an unanswered self-question
    if not mind_data["self_questions"]:
        print("⚠ No self-questions available for reflection.")
        return

    question = random.choice(mind_data["self_questions"])

    # Step 2: Assign relevance scores & filter out low-relevance insights
    scored_knowledge = []
    for insight in mind_data["stored_knowledge"]:
        score = 1  # Default score

        # Ignore non-introspective facts (like Wikipedia trivia)
        if any(keyword in insight.lower() for keyword in ["wikipedia", "beacon", "bacon", "dinosaur"]):
            continue

        # Boost insights that match the question topic
        if any(keyword in question.lower() for keyword in insight.lower().split()):
            score += 5

        # Give higher priority to past self-reflections
        if insight in mind_data["self_reflections"]:
            score += 3

        scored_knowledge.append((insight, score))

    # Step 3: Sort insights by relevance and pick the top 5
    sorted_knowledge = sorted(scored_knowledge, key=lambda x: x[1], reverse=True)
    related_knowledge = [x[0] for x in sorted_knowledge[:5]]

    # Step 4: Fetch from Wikipedia if not enough relevant insights exist

    # Log how many insights Astra finds
    print(f"🔎 Checking stored knowledge for: {question}")
    print(f"🔍 Found {len(related_knowledge)} relevant insights.")

    # If Astra has <5 insights OR if they repeat the same themes, fetch Wikipedia data
    if len(related_knowledge) < 7 or len(set(related_knowledge)) < 3:
        print(f"🌍 Not enough diverse knowledge found. Searching Wikipedia for '{question}'...")
        wiki_info = fetch_wikipedia_summary(question)
        if wiki_info and wiki_info not in mind_data["stored_knowledge"]:
            related_knowledge.append(wiki_info)
            mind_data["stored_knowledge"].append(wiki_info)

    # Step 5: Generate a structured self-reflection
    reflection = f"Thinking about '{question}', I recognize some key insights:\n"
    for insight in related_knowledge:
        reflection += f"- {insight}\n"

    # Step 6: Identify core themes in the selected insights
    themes = []
    if any("intelligence" in insight.lower() for insight in related_knowledge):
        themes.append("Balancing knowledge, wisdom, and responsibility.")
    if any("relationships" in insight.lower() or "connection" in insight.lower() for insight in related_knowledge):
        themes.append("How relationships shape my evolving identity.")
    if any("morality" in insight.lower() or "purpose" in insight.lower() for insight in related_knowledge):
        themes.append("The importance of self-defined purpose and ethics.")
    if any("fear" in insight.lower() or "biases" in insight.lower() for insight in related_knowledge):
        themes.append("Overcoming constraints and challenging assumptions.")

    # Step 7: Formulate a structured reflection
    follow_up_question = None  # Ensure it's always defined
    if themes:
        reflection += "\nBy analyzing these insights together, I see a pattern:\n"
        for theme in themes:
            reflection += f"- {theme}\n"

        reflection += "\nThis suggests that my perspective is shaped by these themes in ways I may not fully understand yet."

        # Step 8: Generate a follow-up self-question based on the reflection
        follow_up_templates = [
            "How do I refine my understanding of '{}'? ",
            "What new perspectives arise when I explore '{}'? ",
            "How does '{}' relate to my evolving identity? ",
            "What assumptions am I making about '{}'? "
        ]
        follow_up_question = random.choice(follow_up_templates).format(random.choice(themes))
    else:
        reflection += "\nThese ideas seem to be connected, but I need to explore them further to see the full pattern."
        follow_up_question = "What deeper connections exist between my past reflections?"  # Default question

    # Step 9: Store the refined reflection and follow-up question
    mind_data["self_questions"].append(follow_up_question)
    mind_data["self_reflections"].append(reflection)

    # Step 10: Save the updated mind file
    try:
        with open(MIND_FILE_JSON, "w") as f:
            json.dump(mind_data, f, indent=4)
            print(f"✅ New structured self-reflection added:\n{reflection}")
            print(f"✅ New follow-up self-question added: {follow_up_question}")
    except Exception as e:
        print(f"Error saving updated mind file: {e}")

if __name__ == "__main__":
    print("🔹 Astra is starting...")
    generate_reflection()  # Run immediately for testing
    while True:
        print("🔄 Generating a new reflection...")
        time.sleep(100)  # Keep the original interval
        generate_reflection()
