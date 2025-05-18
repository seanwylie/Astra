from pathlib import Path
import re

# Files to patch
FILES_TO_PATCH = [
    "astra_core/knowledge.py",
    "astra_core/mood/trust_manager.py",
    "astra_core/astra_schedule/play.py",
    "astra_core/astra_schedule/dream.py",
]

# Replace direct save_mind(...) with SmartMindSession wrapper
def patch_file(filepath: Path):
    original = filepath.read_text()
    modified = original

    # Import injection (only if not present)
    if "SmartMindSession" not in original:
        modified = re.sub(
            r"(import .+?\n)(?!from astra_interfaces\.mind_session)",
            r"\1from astra_interfaces.mind_session import SmartMindSession\n",
            modified,
            count=1,
        )

    # Replace save_mind(...) usage
    def replace_save(match):
        inner = match.group(1).strip()
        return (
            "session = SmartMindSession()\n"
            f"session.data = {inner}\n"
            "session.maybe_save()"
        )

    modified = re.sub(r"save_mind\((.*?)\)", replace_save, modified)

    if modified != original:
        backup_path = filepath.with_suffix(".py.bak")
        filepath.write_text(modified)
        print(f"✅ Patched: {filepath} (backup saved as {backup_path.name})")
        backup_path.write_text(original)
    else:
        print(f"ℹ️ No changes needed: {filepath}")

# Run the patch on all files
if __name__ == "__main__":
    print("🔧 Patching unsafe save_mind(...) calls...")
    for file in FILES_TO_PATCH:
        patch_file(Path(file))
    print("✅ Done.")
