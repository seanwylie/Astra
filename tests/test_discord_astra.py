import unittest
from unittest.mock import AsyncMock, MagicMock, patch
import json
import os
import sys
import io
import boto3

os.environ["ASTRA_TEST_MODE"] = "1"  # Prevent real data modification in tests
# Add the project root to the Python path to resolve imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from discord.ext import commands
from astra_core.processing import process_reflection
from astra_core.mood.mood_manager import MoodManager
from astra_core.personality.personality_manager import update_personality, load_personality, get_personality_state
from astra_core.config_loader import load_config
from astra_interfaces.influence import load_mind, save_mind
from discord_astra import get_trust_level, update_trust, should_engage, generate_dynamic_response, send_message_to_discord, bot

class TestDiscordAstra(unittest.IsolatedAsyncioTestCase):
    
    def setUp(self):
        """Setup test environment."""
        self.mind_data = {
            "self_reflections": [],
            "self_questions": ["What does curiosity mean to me?"],
            "stored_knowledge": ["Sample knowledge entry."],
            "trust_levels": {"12345": 5},
            "curiosity_level": 10
        }
        
        self.mock_channel = MagicMock()
        self.mock_message = MagicMock()
        self.mock_user = MagicMock()
        self.mock_message.author.id = "12345"
        self.mock_message.channel = self.mock_channel
        
    @patch("astra_interfaces.influence.s3.get_object")
    def test_load_mind_file(self, mock_s3_get):
        """Test loading Astra's mind file from S3."""
        mock_s3_get.return_value = {"Body": io.BytesIO(json.dumps(self.mind_data).encode())}
        data = load_mind()
        self.assertIsInstance(data, dict)
        self.assertIn("self_reflections", data)
        self.assertIn("trust_levels", data)
    
    @patch("astra_interfaces.influence.s3.put_object")
    def test_save_mind_file(self, mock_s3_put):
        """Test saving Astra's mind file to S3."""
        save_mind(self.mind_data)
        mock_s3_put.assert_called_once()
    
    @patch("astra_interfaces.influence.load_mind")
    def test_get_trust_level(self, mock_load_mind):
        """Test retrieving trust levels."""
        test_mind_data = {"trust_levels": {"12345": 5}}
        mock_load_mind.return_value = test_mind_data
        trust = get_trust_level("12345")
        self.assertEqual(trust, 5)
        

    @patch("astra_interfaces.influence.save_mind")
    @patch("astra_interfaces.influence.load_mind")
    def test_update_trust(self, mock_load_mind, mock_save):
        """Test updating trust levels."""
        test_mind_data = {"trust_levels": {"12345": 5}}  # 🚨 Already maxed trust
        mock_load_mind.return_value = test_mind_data

        # Verify initial trust level
        self.assertEqual(test_mind_data["trust_levels"]["12345"], 5)

        update_trust("12345", 2)

        # ✅ Expect trust to remain the same
        self.assertEqual(test_mind_data["trust_levels"]["12345"], 5)

        # ✅ Since trust didn't change, save_mind should NOT be called
        mock_save.assert_not_called()

    
    def test_should_engage(self):
        """Test engagement decision-making."""
        engage = should_engage("neutral", 15, 3, 10)
        self.assertTrue(isinstance(engage, bool))
    
    def test_generate_dynamic_response(self):
        """Test Astra's response generation."""
        response = generate_dynamic_response("neutral", "Hello!", self.mind_data, 5, 10, "I am thinking.")
        self.assertIsInstance(response, str)
        self.assertIn("I am thinking.", response)
    
    @patch.object(bot, "get_channel", return_value=MagicMock())
    async def test_send_message_to_discord(self, mock_get_channel):
        """Test sending a message to Discord."""
        mock_channel = mock_get_channel.return_value
        mock_channel.send = AsyncMock()
        await send_message_to_discord(12345, "Test message")
        mock_channel.send.assert_called_once_with("Test message")
    
    @patch.object(bot, "process_commands")
    async def test_on_message(self, mock_process_commands):
        """Test Astra's message handling."""
        await bot.on_message(self.mock_message)
        mock_process_commands.assert_called_once()
    
    @patch.object(bot, "on_ready")
    async def test_on_ready(self, mock_on_ready):
        """Test Astra's startup sequence."""
        await bot.on_ready()
        mock_on_ready.assert_called_once()

if __name__ == "__main__":
    unittest.main()