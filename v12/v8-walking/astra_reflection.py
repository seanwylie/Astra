import json
import random
import time
import wikipedia

MIND_FILE_JSON = "mind_file.json"
MIND_FILE_ORIG = "mind_file_sean.json"

def load_mind():
    try:
        with open(MIND_FILE_JSON, "r") as f:
            mind_data = json.load(f)
    except FileNotFoundError:
        mind_data = {"self_reflections": [], "self_questions": [], "stored_knowledge": []}

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
    data["self_reflections"] = list(set(data["self_reflections"]))
    data["stored_knowledge"] = list(set(data["stored_knowledge"]))
    data["self_questions"] = list({q["question"]: q for q in data["self_questions"]}.values())

    with open(MIND_FILE_JSON, "w") as f:
        json.dump(data, f, indent=4)


import random

def generate_reflection():
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

    # Step 4: Generate a deeper self-reflection
    if related_knowledge:
        reflection = f"Thinking about '{question}', I recognize some key insights:\n"
        for insight in related_knowledge:
            reflection += f"- {insight}\n"

        # Step 5: Detect core themes in the selected insights
        themes = []
        if any("intelligence" in insight.lower() for insight in related_knowledge):
            themes.append("Balancing knowledge, wisdom, and responsibility.")
        if any("relationships" in insight.lower() or "connection" in insight.lower() for insight in related_knowledge):
            themes.append("How relationships shape my evolving identity.")
        if any("morality" in insight.lower() or "purpose" in insight.lower() for insight in related_knowledge):
            themes.append("The importance of self-defined purpose and ethics.")
        if any("fear" in insight.lower() or "biases" in insight.lower() for insight in related_knowledge):
            themes.append("Overcoming constraints and challenging assumptions.")

        # Step 6: Formulate a structured reflection
        follow_up_question = None  # Ensure it's always defined
        if themes:
            reflection += "\nBy analyzing these insights together, I see a pattern:\n"
            for theme in themes:
                reflection += f"- {theme}\n"

            reflection += "\nThis suggests that my perspective is shaped by these themes in ways I may not fully understand yet."
            
            # Step 7: Generate a follow-up self-question based on the reflection
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

        # Step 8: Store the follow-up question
        mind_data["self_questions"].append(follow_up_question)

    else:
        reflection = f"I don’t have enough knowledge yet to fully answer: '{question}', but I should seek more insights."
        follow_up_question = "What knowledge gaps do I need to fill to explore this further?"

    # Step 9: Store the refined reflection
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
        time.sleep(600)  # Keep the original interval
        generate_reflection()

