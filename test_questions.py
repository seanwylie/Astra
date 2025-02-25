import sys
import os
import random

# Add the parent directory (astra_reflections) to sys.path so Python can find `astra_core`
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from astra_core.questions.question_generator import generate_questions
from astra_core.questions.question_utils import generate_category_embeddings, categorize_question
from astra_core.questions.question_flagger import flag_unresolved_question
from astra_core.questions.question_answerer import self_answer_question
from astra_core.questions.question_tracker import track_unresolved_questions
from astra_core.config_loader import load_config
from astra_interfaces.influence import save_mind, load_mind

# Load question configuration
# config_file_path = os.path.join(os.path.dirname(__file__), '../../config/question_config.json')
question_config = load_config("question_config")
print(question_config)
# Generate category embeddings
category_embeddings = generate_category_embeddings(question_config)

# Sample reflection and mind_data for testing
reflection = "What is the purpose of existence and why do we feel emotion?"
mind_data = load_mind()

# Step 1: Generate the questions
generated_questions = generate_questions(reflection, mind_data)

# Step 2: Categorize and flag each generated question
for question in generated_questions:
    # Check if the question is a string or a dictionary
    if isinstance(question, dict):
        print(f"Question before categorizing (dict): {question['question']}")
        # Pass the question string to categorize_question
        category = categorize_question(question['question'], category_embeddings)
    else:
        print(f"Question before categorizing (string): {question}")
        # Directly pass the string to categorize_question
        category = categorize_question(question, category_embeddings)
    
    # Print the categorized question
    print(f"Generated Question: {question}")
    print(f"Category: {category}")
    
    # Step 3: Flag unresolved questions
    is_unresolved = flag_unresolved_question(question, mind_data)
    print(f"Is Unresolved: {is_unresolved}")


# Step 4: Track unresolved questions
updated_mind_data = track_unresolved_questions(mind_data)

# Step 5: Answer the unresolved questions (this can be improved with real knowledge)
unanswered_questions = self_answer_question(updated_mind_data)
print(f"Unanswered Questions: {unanswered_questions}")

# Step 6: Save the updated mind data
save_mind(updated_mind_data)

print("✅ End-to-End Test Complete!")
