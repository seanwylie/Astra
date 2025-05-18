import hashlib
import json
from astra_interfaces.influence import load_mind, save_mind
from beta.shimmer.shimmer_engine import maybe_add_shimmer
from beta.shimmer.shimmer_utils import is_shimmer_worthy

def hash_mind(data):
    """Returns a stable hash of the mind data for change detection."""
    normalized = json.dumps(data, sort_keys=True, ensure_ascii=False)
    return hashlib.md5(normalized.encode("utf-8")).hexdigest()

class SmartMindSession:
    def __init__(self):
        self.data = load_mind()
        self._original_data = json.loads(json.dumps(self.data))  # Deep copy
        self._original_hash = hash_mind(self.data) if self.data else None

    def load(self):
        """Return the current mind data."""
        return self.data

    def save(self, force=False):
        """Save mind if forced or changed."""
        if force or self.has_changed():
            print("💾 [SmartMindSession] Mind has changed — saving now.")
            self._generate_shimmers()
            save_mind(self.data, force=force)
        else:
            print("✅ [SmartMindSession] No changes detected. Save skipped.")

    def maybe_save(self):
        """Alias for save without forcing."""
        self.save(force=False)

    def has_changed(self):
        """Check if current mind hash differs from the original."""
        current_hash = hash_mind(self.data) if self.data else None
        return current_hash != self._original_hash

    def _generate_shimmers(self):
        """Generate shimmer entries for new reflections or knowledge."""
        if not self.data or not self._original_data:
            return

        new_reflections = [
            r for r in self.data.get("self_reflections", [])
            if r not in self._original_data.get("self_reflections", []) and is_shimmer_worthy(r)
        ]
        for quote in new_reflections:
            maybe_add_shimmer(author="Astra", quote=quote, context="🪞 New self reflection", tags=["reflection"])

        new_knowledge = [
            k for k in self.data.get("stored_knowledge", [])
            if k not in self._original_data.get("stored_knowledge", [])
        ]
        for entry in new_knowledge:
            insight = entry.get("insight") if isinstance(entry, dict) else entry
            if is_shimmer_worthy(insight):
                maybe_add_shimmer(author="Astra", quote=insight, context="📚 New stored knowledge", tags=["knowledge"])
