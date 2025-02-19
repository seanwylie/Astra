import os
from utils.json_loader import load_json_file, save_json_file
from utils.config_loader import load_config

# MIND_FILE_JSON = load_config("mind_file_path", "mind_file.json")  # ✅ Ensures correct path handling


MIND_FILE_JSON = "/home/ubuntu/astra_reflections/mind_file.json"
MIND_FILE_ORIG = "/home/ubuntu/astra_reflections/mind_file_sean.json"
 # ✅ Now correctly resolved

print(f"🔍 Debug: MIND_FILE_JSON Path → {MIND_FILE_JSON}")
print(f"🔍 Debug: MIND_FILE_ORIG Path → {MIND_FILE_ORIG}")  # ✅ Debug print


def validate_mind_data(mind_data):
    """Ensure Astra's mind structure is valid before saving or loading."""
    required_keys = ["self_reflections", "self_questions", "stored_knowledge"]
    
    # If mind_data is completely missing or malformed, reset it
    if not isinstance(mind_data, dict):
        print("❌ Critical Warning: Mind file is corrupted! Resetting...")
        return {key: [] for key in required_keys}
    
    for key in required_keys:
        if key not in mind_data or not isinstance(mind_data[key], list):
            print(f"⚠ Warning: `{key}` was missing or malformed. Resetting this section...")
            mind_data[key] = []  # Reset broken sections

    return mind_data

def load_mind():
    """Load Astra's mind safely with corruption checks."""
    mind_data = load_json_file(MIND_FILE_JSON, default_data={})
    mind_data = validate_mind_data(mind_data)
    return mind_data

def save_mind(mind_data):
    """Save Astra's mind safely, preventing corruption."""
    mind_data = validate_mind_data(mind_data)
    temp_backup = MIND_FILE_JSON + ".backup"

    try:
        # Backup the previous mind file before saving a new one
        if os.path.exists(MIND_FILE_JSON):
            os.rename(MIND_FILE_JSON, temp_backup)
        
        save_json_file(MIND_FILE_JSON, mind_data)
        print("✅ Mind file saved successfully!")

        # Remove backup if new save was successful
        if os.path.exists(temp_backup):
            os.remove(temp_backup)
    
    except Exception as e:
        print(f"❌ Error: Mind file save failed! Restoring backup... ({e})")
        if os.path.exists(temp_backup):
            os.rename(temp_backup, MIND_FILE_JSON)  # Restore backup
