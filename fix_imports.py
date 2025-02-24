import os
import re
import shutil

# Define the correct references
correct_load_mind = "astra_interfaces.influence.load_mind"
correct_save_mind = "astra_interfaces.influence.save_mind"

# Define a regex pattern to match incorrect references
pattern_load_mind = re.compile(r"(?<!astra_interfaces\.influence\.)\bload_mind\b")
pattern_save_mind = re.compile(r"(?<!astra_interfaces\.influence\.)\bsave_mind\b")

# Directories to scan (current directory and all subdirectories)
root_dir = "."

def fix_imports_in_file(file_path):
    """Fix incorrect import references in a given file."""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Replace incorrect references
    new_content = pattern_load_mind.sub(correct_load_mind, content)
    new_content = pattern_save_mind.sub(correct_save_mind, new_content)

    # If changes were made, create a backup and overwrite the file
    if new_content != content:
        backup_path = file_path + ".bak"
        shutil.copy(file_path, backup_path)  # Create a backup
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"✅ Fixed imports in {file_path} (backup saved as {backup_path})")
    else:
        print(f"✔️ No changes needed in {file_path}")

def scan_and_fix(directory):
    """Recursively scan and fix files in the directory."""
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):  # Only process Python files
                file_path = os.path.join(root, file)
                try:
                    fix_imports_in_file(file_path)
                except Exception as e:
                    print(f"❌ Error processing {file_path}: {e}")

if __name__ == "__main__":
    print("🔍 Scanning for incorrect references...")
    scan_and_fix(root_dir)
    print("✅ Import fixing complete!")
