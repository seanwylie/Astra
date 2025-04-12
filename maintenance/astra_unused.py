import os
import shutil
import ast

PROJECT_ROOT = "astra_reflections"
ENTRY_FILES = [
    "astra_core/discord_astra.py",
    "astra_core/astra_schedule/schedule.py",
    "astra_core/processing.py",
]
SAFE_EXTENSIONS = [".py", ".json", ".yaml", ".yml"]
BACKUP_DIR = "../backup_unused"

def get_all_project_files():
    all_files = []
    for root, _, files in os.walk(PROJECT_ROOT):
        for file in files:
            if any(file.endswith(ext) for ext in SAFE_EXTENSIONS):
                full_path = os.path.join(root, file)
                all_files.append(os.path.normpath(full_path))
    return all_files

def extract_imports_from_file(file_path):
    """Parse imports from a Python file using AST."""
    used = set()
    try:
        with open(file_path, "r") as f:
            tree = ast.parse(f.read(), filename=file_path)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        used.add(alias.name.split('.')[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        used.add(node.module.split('.')[0])
    except Exception as e:
        print(f"⚠️ Failed to parse {file_path}: {e}")
    return used

def flatten_path(path):
    """Convert 'astra_core/foo/bar.py' into 'bar' and 'foo.bar'."""
    parts = path.replace(".py", "").split(os.sep)
    if "astra_core" in parts:
        idx = parts.index("astra_core")
        parts = parts[idx+1:]
    return set(parts + [".".join(parts)])

def detect_unused_files():
    all_files = get_all_project_files()
    used_names = set()

    for entry in ENTRY_FILES:
        full_path = os.path.join(PROJECT_ROOT, entry)
        if not os.path.exists(full_path):
            print(f"⚠️ Entry file not found: {full_path}")
            continue
        used_names |= extract_imports_from_file(full_path)

    # Add the filename stems (e.g. 'reflection', 'utils_helper') from used files
    used_names |= {os.path.splitext(os.path.basename(f))[0] for f in ENTRY_FILES}

    unused = []
    for file in all_files:
        name_stem = os.path.splitext(os.path.basename(file))[0]
        path_parts = flatten_path(file)

        if not any(name in used_names for name in path_parts):
            unused.append(file)

    return unused

def dry_run():
    unused = detect_unused_files()
    print("\n🧹 Suggested Unused Files:")
    for file in unused:
        print(f"   → {file}")
    print(f"\nTotal: {len(unused)} files\n")

    confirm = input("🚨 Move these to backup? (yes/no): ").strip().lower()
    if confirm != "yes":
        print("❌ Cancelled.")
        return

    os.makedirs(BACKUP_DIR, exist_ok=True)
    for file in unused:
        dest = os.path.join(BACKUP_DIR, os.path.basename(file))
        shutil.move(file, dest)
        print(f"📦 Moved: {file} → {dest}")

    print("✅ All unused files moved.")

if __name__ == "__main__":
    dry_run()
