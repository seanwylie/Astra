import hashlib
import json
from astra_interfaces.influence import load_mind, save_mind

def hash_mind(data):
    """Returns a stable hash of the mind data for change detection."""
    normalized = json.dumps(data, sort_keys=True, ensure_ascii=False)
    return hashlib.md5(normalized.encode("utf-8")).hexdigest()


class SmartMindSession:
    def __init__(self):
        self.data = load_mind()
        self._original_hash = hash_mind(self.data) if self.data else None

    def changed(self):
        """Check if the current mind differs from the original loaded version."""
        if not self.data or not self._original_hash:
            return False
        return hash_mind(self.data) != self._original_hash

    def maybe_save(self, force=False):
        if self.data is None:
            print("🚫 [SmartMindSession] No mind data to save.")
            return

        if force:
            print("💾 [SmartMindSession] Force saving mind...")
            save_mind(self.data)
            return

        if self.changed():
            print("💾 [SmartMindSession] Mind has changed — saving now.")
            save_mind(self.data)
        else:
            print("⏩ [SmartMindSession] No changes detected — skipping save.")
