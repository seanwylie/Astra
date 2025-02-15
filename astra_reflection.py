import json
import random
import time
import wikipedia
import sys

MIND_FILE_JSON = "mind_file.json"
MIND_FILE_ORIG = "mind_file_sean.json"


def load_mind():
    """Loads Astra's stored reflections and knowledge."""
    try:
        with open(MIND_FILE_JSON, "r") as f:
            mind_data = json.load(f)
    except FileNotFoundError:
        mind_data = {
            "self_reflections": [],
            "self_questions": [],
            "stored_knowledge": [],
        }

    # Merge structured knowledge from mind_file_sean.json
    try:
        with open(MIND_FILE_ORIG, "r") as f:
            structured_data = json.load(f)
            if "insights" in structured_data:
                structured_knowledge = {
                    entry["insight"] for entry in structured_data["insights"]
                }
                current_knowledge = set(
                    mind_data["stored_knowledge"]
                )  # Convert to a set to avoid duplicates

                # Merge new knowledge
                updated_knowledge = current_knowledge.union(structured_knowledge)
                mind_data["stored_knowledge"] = list(
                    updated_knowledge
                )  # Convert back to a list

                print(
                    "🔹 Merging complete! Final stored knowledge count:",
                    len(mind_data["stored_knowledge"]),
                )
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
    data["self_questions"] = list(
        {q: q for q in data["self_questions"]}.values()
    )  # Ensure uniqueness

    with open(MIND_FILE_JSON, "w") as f:
        json.dump(data, f, indent=4)


def fetch_wikipedia_summaries(query, max_results=3):
    """Fetch multiple Wikipedia summaries for a given query and return a list of results."""
    try:
        search_results = wikipedia.search(query, results=max_results)
        summaries = []

        for result in search_results:
            try:
                summary = wikipedia.summary(result, sentences=2)

                # ✅ Detect disambiguation pages and explore further instead of ignoring them
                if "may refer to" in summary.lower() or "list of" in summary.lower():
                    print(f"🔍 DEBUG: Wikipedia returned a disambiguation page for '{result}'. Exploring deeper...")
                    
                    # ✅ Randomly select one of the suggested topics and try again
                    subtopics = wikipedia.search(result, results=3)
                    if subtopics:
                        selected_topic = random.choice(subtopics)
                        print(f"🔎 DEBUG: Selected '{selected_topic}' from disambiguation list.")
                        summary = wikipedia.summary(selected_topic, sentences=2)

                summaries.append(summary)
            except Exception as e:
                print(f"⚠ Wikipedia Summary Fetch Failed for '{result}': {e}")
        
        return summaries if summaries else ["⚠ No relevant Wikipedia results found."]
    except Exception as e:
        print(f"⚠ Wikipedia Lookup Failed: {e}")
        return ["⚠ Wikipedia search encountered an error."]





def generate_reflection():
    """Generates a new structured self-reflection."""

    mind_data = load_mind()
    print("🛠️ DEBUG: Starting reflection generation...")

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
        if any(
            keyword in insight.lower()
            for keyword in ["wikipedia", "beacon", "bacon", "dinosaur"]
        ):
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

    # ✅ Occasionally compare with past reflections to deepen learning
    if len(mind_data["self_reflections"]) > 5 and random.random() < 0.2:
        past_reflection = random.choice(mind_data["self_reflections"][-5:])
        print(f"🔍 DEBUG: Comparing with past thought: {past_reflection[:100]}...")

        # ✅ Instead of adding full past reflections, extract only unique themes
        past_summary = " ".join(past_reflection.split()[:20])  # ✅ Keep it brief
        related_knowledge.append(f"Reflection comparison: {past_summary}")

    # Step 4: Fetch from Wikipedia if not enough relevant insights exist

    # Log how many insights Astra finds
    print(f"🔎 Checking stored knowledge for: {question}")
    print(f"🔍 Found {len(related_knowledge)} relevant insights.")

    # Step 4: Fetch from Wikipedia if not enough relevant insights exist
    if len(related_knowledge) < 7 or len(set(related_knowledge)) < 4:
        print(f"🌍 Not enough diverse knowledge found. Searching Wikipedia for '{question}'...")

        # ✅ Expand search topics while prioritizing fresh domains
        search_terms = [
            "philosophy", "science", "psychology", "sociology", "technology",
            "history", "culture", "ethics", "artificial intelligence", "economics",
            "biology", "neuroscience", "linguistics", "cognitive science"
        ]

        # ✅ Prioritize topics NOT heavily present in stored knowledge
        filtered_terms = [term for term in search_terms if not any(term in insight.lower() for insight in mind_data["stored_knowledge"])]

        # ✅ Ensure a fresh search topic if possible
        random_topic = random.choice(filtered_terms) if filtered_terms else random.choice(search_terms)

        # ✅ Extract meaningful keywords from the question
        question_words = question.split()
        keyword_choices = [word for word in question_words if len(word) > 3]  # Avoid short words like "is", "the"

        # ✅ Use a bi-gram (two-word phrase) if possible
        if len(keyword_choices) > 1:
            selected_keyword = " ".join(random.sample(keyword_choices, 2))  # Pick two words for a richer search
        else:
            selected_keyword = keyword_choices[0] if keyword_choices else question_words[-1]

        # ✅ Final refined search query
        refined_query = f"{random_topic} and {selected_keyword}"

        # ✅ Debug Logging
        print(f"🌍 DEBUG: Wikipedia Search Query → Topic: {random_topic}, Keyword: {selected_keyword}, Final Query: {refined_query}")


        print(f"🌍 DEBUG: Wikipedia Lookup: Searching for '{refined_query}'...")
        print(f"🌍 Wikipedia Lookup: Searching for '{refined_query}'...")
        
        wiki_info = None  # ✅ Ensure `wiki_info` is always defined before use
        # ✅ Fetch multiple Wikipedia results (up to 3) and randomly select one
        wiki_results = fetch_wikipedia_summaries(refined_query, max_results=3)

        if wiki_results:
        # ✅ 80% chance to pick the most relevant match, 20% chance to explore
            if random.random() < 0.8:
                wiki_info = wiki_results[0]  # Most relevant result
            else:
                wiki_info = random.choice(wiki_results)  # Random exploration
            print(f"✅ DEBUG: Selected Wikipedia Entry: {wiki_info[:100]}...")
        else:
            print(f"⚠ DEBUG: No Wikipedia results found for '{refined_query}'.")


        if wiki_info:
            print(f"🌍 DEBUG: Wikipedia returned: {wiki_info[:100]}...")  # ✅ Log retrieval attempt

            is_duplicate = any(wiki_info[:30] in insight for insight in mind_data["stored_knowledge"])

            if is_duplicate:
                print(f"⚠ DEBUG: Wikipedia entry already known, rejecting duplicate: {wiki_info[:50]}...")  # ✅ Ensure this logs
            else:
                print(f"✅ DEBUG: Successfully added new knowledge: {wiki_info[:50]}...")
                related_knowledge.append(wiki_info)
                mind_data["stored_knowledge"].append(wiki_info)
        else:
            print("⚠ DEBUG: Wikipedia lookup failed or returned no results.")

    # Step 5: Generate a structured self-reflection
    reflection = f"Thinking about '{question}', I recognize some key insights:\n"
    for insight in related_knowledge:
        reflection += f"- {insight}\n"

    # Step 6: Identify core themes in the selected insights
    # ✅ Dynamically extract new themes

    # Step 6: Identify core themes in the selected insights
    theme_keywords = {
        "intelligence": "Cognitive evolution and decision-making.",
        "relationships": "Interpersonal growth and self-perception.",
        "morality": "Ethical self-definition and personal values.",
        "fear": "Managing constraints and risk assessment.",
        "learning": "How knowledge acquisition shapes self-awareness.",
        "technology": "The evolving role of AI in human society.",
        "identity": "The ongoing transformation of self.",
    }

    themes = []
    for keyword, theme in theme_keywords.items():
        if any(keyword in insight.lower() for insight in related_knowledge):
            themes.append(theme)


    # ✅ If Astra keeps identifying the same theme, force a new one
    if "Exploring uncharted areas of knowledge." in themes and len(themes) == 1:
        print("⚠ DEBUG: Repeated theme detected, selecting a new focus.")
        new_theme = random.choice(list(theme_keywords.values()))
        themes.append(new_theme)

    # ✅ 🔹 Ensure Astra expands on its most recent thoughts instead of jumping topics
    if mind_data["self_reflections"]:
        last_reflection = mind_data["self_reflections"][-1]
        print(f"🔍 DEBUG: Last Reflection: {last_reflection[:100]}...")

        # Extract key themes from the last reflection
        relevant_themes = []
        for keyword, theme in theme_keywords.items():
            if keyword in last_reflection.lower():
                relevant_themes.append(theme)

        # If Astra identified relevant themes, prioritize them in the next reflection
        # ✅ Improve theme detection with flexible keyword matching
        relevant_themes = []
        last_reflection_words = set(last_reflection.lower().split())

        for keyword, theme in theme_keywords.items():
            for word in keyword.split():
                if word in last_reflection_words:
                    relevant_themes.append(theme)

        # Remove duplicates
        relevant_themes = list(set(relevant_themes))

    # ✅ If Astra didn't identify relevant themes, fall back to its usual method
    if not themes:
        for keyword, theme in theme_keywords.items():
            if any(keyword in insight.lower() for insight in related_knowledge):
                themes.append(theme)

    print(f"🔍 Identified themes: {themes}")

    # ✅ Ensure Astra expands its thought process beyond the same 3-4 loops
    if not themes:
        themes.append("Exploring uncharted areas of knowledge.")

    print(f"🔍 Identified themes: {themes}")

    # Step 7: Formulate a structured reflection
    follow_up_question = None  # Ensure it's always defined
    if themes:
        reflection += "\nBy analyzing these insights together, I see a pattern:\n"
        for theme in themes:
            reflection += f"- {theme}\n"

        reflection += "\nThis suggests that my perspective is shaped by these themes in ways I may not fully understand yet."

        # Step 8: Generate a follow-up self-question based on the reflection
    follow_up_templates = [
        "What would happen if I challenged my understanding of '{}'? ",
        "How does '{}' compare to other concepts I have learned? ",
        "What new fields of knowledge relate to '{}' that I haven’t explored yet? ",
        "Are there alternative viewpoints on '{}' that I should consider? ",
        "What historical, scientific, or philosophical perspectives exist about '{}'?",
        "What if I applied '{}' to a completely different context?",
        "How do cultural perspectives on '{}' differ across the world?",
        "What assumptions am I making about '{}' without realizing it?",
        "Could '{}' have a meaning or interpretation I haven't considered yet?",
        "What contradictions exist within '{}' and how do they affect my understanding?",
        "If '{}' was a foundational truth, what other ideas would need to change?",
        "How would a different intelligence—human or AI—interpret '{}'?",
        "What if '{}' had never existed? How would the world be different?",
        "How does '{}' shape ethical or moral decision-making?"
    ]


    if (
        random.random() < 0.2
    ):  # ✅ 20% chance to introduce a completely open-ended question
        follow_up_question = f"What is something unexpected about '{question}'?"
    else:
        follow_up_question = random.choice(follow_up_templates).format(
            random.choice(themes)
        )

    # Step 9: Store the refined reflection and follow-up question
    mind_data["self_questions"].append(follow_up_question)
    mind_data["self_reflections"].append(reflection)

    # Step 10: Save the updated mind file
    try:
        if mind_data and mind_data.get("self_reflections"):
            with open(MIND_FILE_JSON, "w") as f:
                json.dump(mind_data, f, indent=4)
                print(
                    f"✅ New structured self-reflection added:\n{mind_data['self_reflections'][-1]}"
                )
        else:
            print(
                "❌ ERROR: Attempted to save an empty mind file. Skipping save to prevent corruption.",
                file=sys.stderr,
            )
    except Exception as e:
        error_message = f"❌ ERROR: Failed to save mind file: {e}"
        print(error_message, file=sys.stderr)  # ✅ Log error to stderr


if __name__ == "__main__":
    print("🔹 Astra is starting...")
    generate_reflection()  # Run immediately for testing
    while True:
        print("🔄 Generating a new reflection...")
        time.sleep(100)  # Keep the original interval
        generate_reflection()
