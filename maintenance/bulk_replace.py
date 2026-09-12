#!/usr/bin/env python3
import os
import re
import argparse
import difflib
from pathlib import Path

def parse_arguments():
    parser = argparse.ArgumentParser(description="Recursively search and replace text in files.")
    parser.add_argument("search", help="Regex pattern to search for.")
    parser.add_argument("replace", help="Replacement string.")
    parser.add_argument("-i", "--import-line", help="Import line to inject if missing (e.g. 'from x import y').")
    parser.add_argument("-p", "--path", default=".", help="Root directory to start the search (default: current directory).")
    parser.add_argument("-g", "--glob", default="*.py", help="Glob pattern to match files (default: *.py).")
    parser.add_argument("-f", "--force", action="store_true", help="Force replacement even if no changes detected.")
    parser.add_argument("-d", "--dry-run", action="store_true", help="Perform a dry run without modifying files.")
    parser.add_argument("-b", "--backup", action="store_true", help="Create a backup of each file before modifying.")
    return parser.parse_args()

def generate_diff(original, modified, filename):
    diff = difflib.unified_diff(
        original.splitlines(keepends=True),
        modified.splitlines(keepends=True),
        fromfile=f"{filename} (original)",
        tofile=f"{filename} (modified)",
        lineterm=""
    )
    return ''.join(diff)

def inject_import_if_missing(content, import_line):
    if import_line in content:
        return content, False

    lines = content.splitlines(keepends=True)
    insert_index = 0

    # Insert after last import
    for i, line in enumerate(lines):
        if line.strip().startswith("import") or line.strip().startswith("from"):
            insert_index = i + 1

    lines.insert(insert_index, import_line + "\n")
    return ''.join(lines), True

def process_file(file_path, search_pattern, replacement, args):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            original_content = file.read()
    except (UnicodeDecodeError, OSError) as e:
        print(f"⚠️ Skipping {file_path}: {e}")
        return

    if not search_pattern.search(original_content):
        print(f"ℹ️ No match for pattern in {file_path}")
        return

    modified_content = re.sub(search_pattern, replacement, original_content)

    import_added = False
    if args.import_line:
        modified_content, import_added = inject_import_if_missing(modified_content, args.import_line)

    if original_content != modified_content or args.force:
        print(f"\n🔍 Changes in {file_path}:")
        diff = generate_diff(original_content, modified_content, file_path)
        print(diff)

        if not args.dry_run:
            if args.backup:
                backup_path = file_path.with_suffix(file_path.suffix + ".bak")
                try:
                    with open(backup_path, 'w', encoding='utf-8') as backup_file:
                        backup_file.write(original_content)
                    print(f"🗂️ Backup created at {backup_path}")
                except OSError as e:
                    print(f"❌ Failed to create backup for {file_path}: {e}")
                    return

            try:
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(modified_content)
                print(f"✅ Updated {file_path}")
                if import_added:
                    print(f"➕ Injected import: {args.import_line}")
            except OSError as e:
                print(f"❌ Failed to write changes to {file_path}: {e}")
    else:
        print(f"ℹ️ No changes in {file_path}")

def main():
    args = parse_arguments()
    search_pattern = re.compile(args.search)

    root_path = Path(args.path)
    if not root_path.is_dir():
        print(f"❌ The path {args.path} is not a valid directory.")
        return

    matched_files = list(root_path.rglob(args.glob))
    if not matched_files:
        print(f"🔍 No files matching pattern '{args.glob}' found in {args.path}")
        return

    for file_path in matched_files:
        if file_path.is_file():
            process_file(file_path, search_pattern, args.replace, args)

if __name__ == "__main__":
    main()
