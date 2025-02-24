import json
import os
from datetime import datetime
from astra_interfaces.influence import load_mind, save_mind

# File paths
LOG_FILE_PATH = "astra_logs.json"  # Ensure this points to Astra's log file
SNAPSHOT_DIR = "snapshots/"  # Directory for saving snapshots
MAX_SNAPSHOT_AGE_DAYS = 7  # Define the maximum age of snapshots (in days)

def load_logs():
    """Load the log file and return the latest logs."""
    try:
        with open(LOG_FILE_PATH, 'r') as f:
            logs = [json.loads(line) for line in f.readlines()]
        return logs
    except (FileNotFoundError, json.JSONDecodeError):
        print("🚨 Error: log file not found or corrupt.")
        return []

def check_health(mind_data):
    """Assess Astra's health based on emotional, cognitive, and ethical indicators."""
    health = {}

    # 1. Emotional & Ethical Health
    current_mood = mind_data.get("last_mood", "Unknown")
    health['mood_stability'] = current_mood
    health['ethical_alignment'] = "Good" if "thoughtfulness" in current_mood.lower() else "Check needed"

    # 2. Cognitive Health (memory and knowledge)
    health['memory_health'] = "Good" if len(mind_data.get("self_reflections", [])) > 50 else "Needs attention"
    
    # 3. Decision-Making & Trust (trust levels and self-assessments)
    trust_levels = mind_data.get("trust_levels", {})
    health['decision_making'] = "Aligned" if len(trust_levels) > 0 else "Needs improvement"
    health['trust_system'] = "Stable" if trust_levels else "Needs attention"

    # 4. Self-Reflection & Introspection
    health['self_reflection'] = "Adequate" if len(mind_data.get('self_reflections', [])) > 10 else "Needs more reflection"

    return health

def generate_health_report(mind_data, logs):
    """Generate a comprehensive checkup report based on Astra's health."""
    # Get the current health indicators
    health = check_health(mind_data)

    # Print Checkup Report
    print("🔍 Astra's Checkup Report")
    print("---------------------------")
    print(f"Current Mood: {mind_data.get('last_mood', 'Unknown')}")
    print(f"Curiosity Level: {mind_data.get('curiosity_level', 1.0)}")
    print(f"Mood Score: {mind_data.get('mood_score', 0.0)}")
    print(f"Trust Levels: {mind_data.get('trust_levels', {})}")
    print(f"Reflections Count: {len(mind_data.get('self_reflections', []))}")
    print(f"Questions Count: {len(mind_data.get('self_questions', []))}")
    print(f"Stored Knowledge Count: {len(mind_data.get('stored_knowledge', []))}")
    print(f"Self-Assessments Count: {len(mind_data.get('self_assessments', []))}")
    print(f"Biases Count: {len(mind_data.get('biases', []))}")
    print("\n🔍 Recent Logs (Last 5):")
    for log in logs[-5:]:
        print(f" - {log}")

    # Sampling Astra's Mind: Reflections, Self-Questions, Knowledge
    print("\n🔍 Sampling Astra's Mind:")
    print("---------------------------")
    print("\nReflections (Last 5):")
    for reflection in mind_data.get('self_reflections', [])[-5:]:
        print(f" - {reflection}")
    
    print("\nSelf-Questions (Last 5):")
    for question in mind_data.get('self_questions', [])[-5:]:
        print(f" - {question}")
    
    print("\nStored Knowledge (Last 5):")
    for knowledge in mind_data.get('stored_knowledge', [])[-5:]:
        print(f" - {knowledge}")

    # Display Health Status
    print("\n🔍 Health Indicators:")
    for key, value in health.items():
        print(f" - {key.replace('_', ' ').capitalize()}: {value}")

    # Snapshot and log wipe
    snapshot_filename = f"{SNAPSHOT_DIR}snapshot_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json"
    with open(snapshot_filename, 'w') as snapshot_file:
        json.dump(mind_data, snapshot_file, indent=4)
    print(f"🔍 Snapshot saved to {snapshot_filename}")

    # Clean up old snapshots
    clean_old_snapshots()

    with open(LOG_FILE_PATH, 'w') as log_file:
        log_file.write('')
    print("🔍 Logs wiped for new session.")

def clean_old_snapshots():
    """Deletes snapshots older than the specified number of days."""
    now = datetime.now()
    for snapshot_filename in os.listdir(SNAPSHOT_DIR):
        snapshot_path = os.path.join(SNAPSHOT_DIR, snapshot_filename)
        if snapshot_filename.endswith(".json"):
            try:
                # Extract the timestamp portion of the snapshot filename
                snapshot_time_str = snapshot_filename.split('_')[1]
                snapshot_time = datetime.strptime(snapshot_time_str, "%Y-%m-%d")
                if (now - snapshot_time).days > MAX_SNAPSHOT_AGE_DAYS:
                    os.remove(snapshot_path)
                    print(f"🔍 Deprecated snapshot removed: {snapshot_filename}")
            except Exception as e:
                print(f"🚨 Error processing snapshot {snapshot_filename}: {e}")

def check_up():
    """Performs a checkup on Astra’s state and prints a report."""
    # Load Astra's mind data and logs
    mind_data = load_mind()
    logs = load_logs()

    # Generate the health check report
    generate_health_report(mind_data, logs)
    
# Run the checkup
if __name__ == "__main__":
    check_up()
