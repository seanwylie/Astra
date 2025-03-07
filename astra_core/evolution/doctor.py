import os
import shutil
import difflib
import subprocess
from astra_core.config_loader import load_config  # ✅ Load Astra's configurations

# ✅ Load evolution settings
doctor_config = load_config("doctor_config")
BACKUP_DIR = doctor_config.get("backup_directory", "astra_core/evolution/backups")
SANDBOX_SCRIPT = "astra_core/evolution/sandbox/test_script.py"

# ✅ Ensure backup directory exists
os.makedirs(BACKUP_DIR, exist_ok=True)

def create_backup(target_file):
    """Creates a backup before Astra modifies a critical file."""
    if not os.path.exists(target_file):
        print(f"⚠ WARNING: {target_file} does not exist. Skipping backup.")
        return None

    backup_path = os.path.join(BACKUP_DIR, os.path.basename(target_file) + ".bak")
    shutil.copy2(target_file, backup_path)
    print(f"🛡️ Backup created: {backup_path}")
    return backup_path

def compare_changes(original_file, modified_file):
    """Compares changes between original and modified files."""
    with open(original_file, "r", encoding="utf-8") as f1, open(modified_file, "r", encoding="utf-8") as f2:
        original_lines = f1.readlines()
        modified_lines = f2.readlines()

    diff = list(difflib.unified_diff(original_lines, modified_lines, lineterm=""))
    return diff if diff else None

def run_sandbox_test():
    """Executes Astra’s full validation test before applying changes."""
    if not os.path.exists(SANDBOX_SCRIPT):
        print(f"⚠ No test script found! Astra needs to create one.")
        return False

    print("🔬 Running Astra's expanded test suite...")
    result = subprocess.run(["python3", SANDBOX_SCRIPT], capture_output=True, text=True)

    print("📜 Output:")
    print(result.stdout.strip())

    return result.returncode == 0

def rollback_file(target_file, backup_path):
    """Restores a file to its last known good state if changes fail."""
    if backup_path and os.path.exists(backup_path):
        print(f"🚨 Test failed! Rolling back {target_file} to previous version.")
        shutil.copy2(backup_path, target_file)
        print(f"✅ Rollback successful: {target_file} restored.")
    else:
        print(f"⚠ WARNING: No backup available for {target_file}. Manual intervention required!")

def validate_modifications(target_file):
    """Checks Astra’s modifications before finalizing."""
    print(f"🩺 Running Doctor checks on {target_file}...")

    backup_path = create_backup(target_file)

    if not run_sandbox_test():
        rollback_file(target_file, backup_path)
        return False

    diff = compare_changes(backup_path, target_file) if backup_path else None
    if diff:
        print(f"🔍 Changes detected in {target_file}:\n" + "\n".join(diff[:10]) + ("\n..." if len(diff) > 10 else ""))
    else:
        print(f"✅ No significant changes detected in {target_file}.")

    print(f"✅ All changes are valid! Astra's modifications pass.")
    return True

if __name__ == "__main__":
    target_files = ["astra_core/processing.py", "astra_core/discord_astra.py"]
    for file in target_files:
        validate_modifications(file)
