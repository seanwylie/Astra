from app.interfaces.smart_mind_session import SmartMindSession

class MindAccess:
    def __init__(self):
        self.session = SmartMindSession()
        self.data = self.session.data

    def store_knowledge(self, new_insight):
        if not self.data:
            print("🚨 [MindAccess] No memory available. Skipping knowledge storage.")
            return

        print(f"🧠 [MindAccess] Attempting to store knowledge: {new_insight[:100]}...")
        if new_insight in self.data.get("stored_knowledge", []):
            print("⚠ [MindAccess] Insight already exists. Skipping.")
            return

        self.data["stored_knowledge"].append(new_insight)
        self.session.maybe_save()
        print("📄 [MindAccess] Knowledge saved successfully!")
