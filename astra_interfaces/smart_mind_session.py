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

    def load(self):
        """Return the current mind data."""
        return self.data

    def save(self, force=False):
        """Save mind if forced or changed."""
        if force:
            print("💾 [SmartMindSession] Force saving mind...")
            save_mind(self.data, force=True)
            return

        if self.has_changed():
            print("💾 [SmartMindSession] Mind has changed — saving now.")
            save_mind(self.data)
        else:
            print("✅ [SmartMindSession] No changes detected. Save skipped.")

    def maybe_save(self):
        """Alias for save without forcing."""
        self.save(force=False)

    def has_changed(self):
        """Check if current mind hash differs from the original."""
        current_hash = hash_mind(self.data) if self.data else None
        return current_hash != self._original_hash
