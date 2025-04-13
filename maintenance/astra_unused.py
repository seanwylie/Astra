import os
import ast
import shutil
from collections import defaultdict

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
EXCLUDE_DIRS = {"venv", "__pycache__", "logs", "maintenance", "backup", ".git"}
BACKUP_DIR = os.path.abspath(os.path.join(ROOT_DIR, "../backup"))

IMPORT_LOOKUP = set()
PYTHON_FILES = []
AUXILIARY_FILES = []

CATEGORY_RULES = {
    "tests": ["test", "diagnostic", "sandbox"],
    "mind": ["mind_file", "self_reflections", "self_questions", "stored_knowledge", "past_conversations"],
    "logs": ["log"],
    "configs": [".json", "config"],
    "utils": ["helper", "utils", "loader"],
    "deprecated": ["old", "legacy", "refactor"],
    "evolution": ["evolution", "doctor", "splitter"],
    "ethics": ["spark", "ethics"],
    "schedules": ["schedule", "dinner", "sleep", "dream", "school", "play"],
}

def gather_all_py_files():
    for dirpath, dirnames, filenames in os.walk(ROOT_DIR):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]

        for filename in filenames:
            full_path = os.path.join(dirpath, filename)
            if filename.endswith(".py"):
                PYTHON_FILES.append(full_path)
            elif not filename.endswith(".pyc") and not filename.endswith(".log"):
                AUXILIARY_FILES.append(full_path)

def extract_imports_from_file(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            node = ast.parse(f.read(), filename=filepath)
        for n in ast.walk(node):
            if isinstance(n, ast.Import):
                for alias in n.names:
                    IMPORT_LOOKUP.add(alias.name.split(".")[0])
            elif isinstance(n, ast.ImportFrom):
                if n.module:
                    IMPORT_LOOKUP.add(n.module.split(".")[0])
    except Exception as e:
        print(f"⚠️ Skipped {filepath} (parse error): {e}")

def categorize(path):
    fname = os.path.basename(path).lower()
    for category, keywords in CATEGORY_RULES.items():
        if any(k in fname for k in keywords):
            return category
    return "misc"

def move_to_backup(path, category):
    rel_path = os.path.relpath(path, ROOT_DIR)
    dest_dir = os.path.join(BACKUP_DIR, category)
    os.makedirs(dest_dir, exist_ok=True)
    dest_path = os.path.join(dest_dir, os.path.basename(path))
    shutil.move(path, dest_path)
    print(f"📦 Moved: {rel_path} → {os.path.relpath(dest_path, ROOT_DIR)}")

def confirm_file_action(file_path):
    """Prompt for confirmation on each file."""
    while True:
        choice = input(f"\nMove '{os.path.relpath(file_path, ROOT_DIR)}'? (y/n/a to move all remaining in category): ").strip().lower()
        if choice in {"y", "n", "a"}:
            return choice
        else:
            print("❓ Please enter 'y' to move, 'n' to skip, or 'a' to move all remaining in this category.")

def main():
    print(f"🔍 Scanning: {ROOT_DIR}")
    gather_all_py_files()

    # Extract imports from all project files
    for py_file in PYTHON_FILES:
        extract_imports_from_file(py_file)

    # Determine unused Python files
    unused_py = []
    for py_file in PYTHON_FILES:
        name = os.path.splitext(os.path.basename(py_file))[0]
        if name not in IMPORT_LOOKUP and "main" not in name and "discord_astra" not in name:
            unused_py.append(py_file)

    # Determine auxiliary files not used
    unused_aux = [
        f for f in AUXILIARY_FILES
        if not f.endswith(".env") and not f.endswith(".md")
    ]

    all_suggestions = unused_py + unused_aux
    categorized = defaultdict(list)
    for file in all_suggestions:
        category = categorize(file)
        categorized[category].append(file)

    if not all_suggestions:
        print("✅ Nothing unused found. Your Astra is tidy!")
        return

    print("\n🧹 Suggested Unused Files:")

    for category, files in categorized.items():
        print(f"\n📁 {category.capitalize()} ({len(files)} files)")
        skip_remaining = False

        for file in files:
            if skip_remaining:
                move_to_backup(file, category)
                continue

            choice = confirm_file_action(file)

            if choice == "y":
                move_to_backup(file, category)
            elif choice == "a":
                move_to_backup(file, category)
                skip_remaining = True
            else:
                print(f"⏭️ Skipped: {os.path.relpath(file, ROOT_DIR)}")

    print("✅ Cleanup session complete.")

if __name__ == "__main__":
    main()
