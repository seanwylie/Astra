#!/usr/bin/env python3
import os
import ast
import json
import time
from pathlib import Path

OUTPUT_FILE = Path(__file__).parent.parent / "file_structure.json"

ENRICHABLE_KEYS = {
    "purpose",
    "refactor_risk_score",
    "performance_issues",
    "code_quality_score",
    "comment_ratio_override"
}

def extract_metadata(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        source = f.read()

    node = ast.parse(source)
    functions = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
    classes = [n.name for n in node.body if isinstance(n, ast.ClassDef)]
    imports = []
    for n in ast.walk(node):
        if isinstance(n, ast.Import):
            for alias in n.names:
                imports.append(alias.name)
        elif isinstance(n, ast.ImportFrom):
            if n.module:
                for alias in n.names:
                    imports.append(f"{n.module}.{alias.name}")

    lines = source.splitlines()
    total_lines = len(lines)
    comment_lines = len([l for l in lines if l.strip().startswith("#")])
    comment_ratio = round(comment_lines / total_lines, 2) if total_lines else 0.0

    return {
        "functions": functions,
        "classes": classes,
        "imports": sorted(set(imports)),
        "line_count": total_lines,
        "comment_ratio": comment_ratio,
    }

def classify_layer(path):
    if "schedule" in path:
        return "behavior"
    if "emotion" in path or "mood" in path:
        return "emotional"
    if "ethic" in path or "spark" in path:
        return "ethical"
    if "knowledge" in path or "reflection" in path:
        return "cognitive"
    if "dinner" in path:
        return "relational"
    if "message" in path or "discord" in path:
        return "communication"
    return "unknown"

def resolve_module_to_path(module_name, all_paths):
    """
    Convert module name (e.g., 'astra_core.dream.dream_seed_logger') to relative path.
    Only resolves if it's in known files.
    """
    candidate_path = module_name.replace(".", "/") + ".py"
    for path in all_paths:
        if path.endswith(candidate_path):
            return path
    return None

def extract_structure(base_dir="astra_core"):
    structure = []
    all_files = list(Path(base_dir).rglob("*.py"))
    file_map = {str(f): extract_metadata(f) for f in all_files}

    # First pass: generate initial structure
    for file_path, metadata in file_map.items():
        info = {
            "path": str(file_path),
            "size_bytes": Path(file_path).stat().st_size,
            "last_modified": Path(file_path).stat().st_mtime,
            **metadata,
            "calls_config_loader": any("config_loader" in imp for imp in metadata["imports"]),
            "calls_session_load": any("mind_session.session" in imp and "load" in imp for imp in metadata["imports"]),
            "calls_save_mind": any("save_mind" in imp for imp in metadata["imports"]),
            "likely_entrypoint": "__main__" in open(file_path, encoding="utf-8").read(),
            "has_test_file": Path("tests") / Path(file_path).name.replace(".py", "_test.py") in Path("tests").rglob("*"),
            "layer": classify_layer(file_path),
            "purpose": "TBD",
            "uses": [],       # to be populated in second pass
            "used_by": [],    # to be populated in second pass
            "refactor_risk_score": None
        }
        structure.append(info)

    # Second pass: resolve dependency relationships
    path_map = {entry["path"]: entry for entry in structure}
    all_paths = list(path_map.keys())

    for entry in structure:
        for imp in entry["imports"]:
            resolved_path = resolve_module_to_path(imp, all_paths)
            if resolved_path:
                entry["uses"].append(resolved_path)
                path_map[resolved_path]["used_by"].append(entry["path"])

    return structure

def merge_with_existing(new_data, existing_data):
    existing_lookup = {entry["path"]: entry for entry in existing_data}
    merged = []

    for entry in new_data:
        path = entry["path"]
        if path in existing_lookup:
            preserved = {
                key: existing_lookup[path].get(key)
                for key in ENRICHABLE_KEYS
                if existing_lookup[path].get(key) is not None
            }
            entry.update(preserved)
        merged.append(entry)

    return merged

def main():
    print("🔍 Scanning file structure...")
    new_structure = extract_structure()

    if Path(OUTPUT_FILE).exists():
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            existing_structure = json.load(f)
    else:
        existing_structure = []

    merged_structure = merge_with_existing(new_structure, existing_structure)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(merged_structure, f, indent=2)

    print(f"✅ Saved updated structure to {OUTPUT_FILE} ({len(merged_structure)} files).")

if __name__ == "__main__":
    main()
