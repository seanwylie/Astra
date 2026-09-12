#!/usr/bin/env python3
"""
Detect import cycles in the app package.
Uses ast to parse Python files and extract import statements, then finds
strongly connected components (cycles) in the import graph.
Output: list of cycles for documentation; no fix applied.
"""
from __future__ import annotations

import ast
import os
from collections import defaultdict
from pathlib import Path

# Project root and app package
PROJECT_ROOT = Path(__file__).resolve().parent.parent
APP_DIR = PROJECT_ROOT / "app"
IGNORE_DIRS = {"__pycache__", ".venv", "venv", ".git"}


def get_app_modules() -> dict[str, str]:
    """Map module name (e.g. app.core.foo) to relative path."""
    modules = {}
    for root, dirs, files in os.walk(APP_DIR):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for f in files:
            if f.endswith(".py") and not f.startswith("_"):
                path = Path(root) / f
                rel = path.relative_to(PROJECT_ROOT)
                # app/core/foo/bar.py -> app.core.foo.bar (strip .py)
                parts = rel.with_suffix("").parts
                mod = ".".join(parts)
                modules[mod] = str(rel)
    return modules


def resolve_import(imp: str, from_mod: str) -> str | None:
    """Resolve relative/absolute import to full module name within app."""
    parts = from_mod.split(".")
    if imp.startswith("."):
        # Relative: .foo -> same package; ..foo -> parent package
        level = 0
        for c in imp:
            if c == ".":
                level += 1
            else:
                break
        name = imp[level:]
        if level > len(parts):
            return None
        base = ".".join(parts[: len(parts) - level]) if level else from_mod
        if name:
            return f"{base}.{name}" if base else name
        return base
    if imp.startswith("app."):
        return imp
    # Top-level (e.g. json, boto3) - we only care about app
    return None


def imports_from_file(path: Path, from_mod: str) -> set[str]:
    """Parse file and return set of resolved app module names it imports."""
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return set()
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return set()
    out = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("app."):
                    out.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module and (node.module.startswith("app.") or (node.level and node.level > 0)):
                resolved = resolve_import(
                    (node.module or "") + ("." + node.names[0].name if node.names else ""),
                    from_mod,
                )
                if not resolved:
                    if node.module and node.module.startswith("app."):
                        base = node.module
                        if node.names:
                            base = f"{node.module}.{node.names[0].name.split('.')[0]}"
                        out.add(base)
                elif resolved:
                    # Add top-level app submodule only for cycle graph
                    top = resolved.split(".")[:3]  # app.core.foo
                    out.add(".".join(top))
    return out


def build_graph(modules: dict[str, str]) -> defaultdict[set]:
    """Build directed graph: module -> set of modules it imports (within app)."""
    graph = defaultdict(set)
    for mod, rel_path in modules.items():
        path = PROJECT_ROOT / rel_path
        if not path.exists():
            continue
        for imp in imports_from_file(path, mod):
            if not imp.startswith("app."):
                continue
            # Normalize to 3 segments for cycle detection
            imp_parts = imp.split(".")
            imp_short = ".".join(imp_parts[:3]) if len(imp_parts) >= 3 else imp
            mod_short = ".".join(mod.split(".")[:3])
            if imp_short != mod_short:
                graph[mod_short].add(imp_short)
    return graph


def find_cycles(graph: defaultdict[set]) -> list[list[str]]:
    """Find strongly connected components (cycles) via DFS."""
    all_nodes = set(graph) | {n for s in graph.values() for n in s}
    index: dict[str, int] = {}
    lowlink: dict[str, int] = {}
    on_stack: dict[str, bool] = {}
    stack: list[str] = []
    cycles: list[list[str]] = []
    counter = [0]

    def strongconnect(v: str) -> None:
        index[v] = counter[0]
        lowlink[v] = counter[0]
        counter[0] += 1
        stack.append(v)
        on_stack[v] = True
        for w in graph.get(v, set()):
            if w not in index:
                strongconnect(w)
                lowlink[v] = min(lowlink[v], lowlink[w])
            elif on_stack.get(w):
                lowlink[v] = min(lowlink[v], index[w])
        if lowlink[v] == index[v]:
            scc = []
            while True:
                w = stack.pop()
                on_stack[w] = False
                scc.append(w)
                if w == v:
                    break
            if len(scc) > 1:
                cycles.append(scc)

    for node in sorted(all_nodes):
        if node not in index:
            strongconnect(node)
    return cycles


def main() -> None:
    modules = get_app_modules()
    graph = build_graph(modules)
    cycles = find_cycles(graph)
    if cycles:
        print("Import cycles detected (app package, normalized to 3 segments):")
        for i, c in enumerate(cycles, 1):
            print(f"  Cycle {i}: {' -> '.join(c)} -> {c[0]}")
    else:
        print("No import cycles detected in app package (within 3-segment module names).")


if __name__ == "__main__":
    main()
