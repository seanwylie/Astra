import unittest
from astra_core.personality.personality_manager import update_personality, load_personality, save_personality

class TestPersonality(unittest.TestCase):

    def setUp(self):
        """Reset personality before each test."""
        self.personality = {"trait_weights": {"thoughtfulness": 1.0, "curiosity": 1.0}}
        save_personality(self.personality)

    def test_deep_conversation(self):
        """Check if 'deep_conversation' increases thoughtfulness and curiosity."""
        update_personality("deep_conversation")
        personality = load_personality()
        self.assertGreater(personality["trait_weights"]["thoughtfulness"], 1.0)
        self.assertGreater(personality["trait_weights"]["curiosity"], 1.0)

    def test_betrayed_trust(self):
        """Check if 'betrayed_trust' decreases trust and increases skepticism."""
        update_personality("betrayed_trust")
        personality = load_personality()
        self.assertLess(personality["trait_weights"]["trust"], 1.0)
        self.assertGreater(personality["trait_weights"]["skepticism"], 1.0)

    def test_boundaries(self):
        """Ensure traits do not exceed min/max bounds."""
        for _ in range(50):  # Over-apply updates
            update_personality("deep_conversation", magnitude=1.0)
        personality = load_personality()
        self.assertLessEqual(personality["trait_weights"]["thoughtfulness"], 1.5)

if __name__ == '__main__':
    unittest.main()
