#!/usr/bin/env python3
"""
Quick test script for the new Creative Expression System
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from beta.services.creative_service import creative_service
from beta.services.personality_service import personality_service

def test_creative_system():
    """Test the creative system functionality"""
    print("🎨 Testing Astra's Creative Expression System\n")
    
    # Test different personality modes
    modes = ['curious', 'analytical', 'creative', 'mentor', 'philosophical', 'balanced']
    
    for mode in modes:
        print(f"🎭 Testing {mode.title()} Mode:")
        print("=" * 40)
        
        # Switch to this personality mode
        personality_service.switch_personality_mode(mode)
        
        # Test poem creation
        print("1. Creating a poem...")
        poem = creative_service.create_poem("wonder", "test_user")
        print(f"   {poem[:100]}...\n")
        
        # Test story creation
        print("2. Writing a story...")
        story = creative_service.write_story("a curious AI discovers creativity", "test_user")
        print(f"   {story[:100]}...\n")
        
        # Test art prompt generation
        print("3. Generating art prompt...")
        art_prompt = creative_service.generate_art_prompt("a mystical forest", "test_user")
        print(f"   {art_prompt[:100]}...\n")
        
        # Test music composition
        print("4. Composing music...")
        music = creative_service.compose_music(None, "test_user")
        print(f"   {music[:100]}...\n")
        
        # Test creative exercise
        print("5. Getting creative exercise...")
        exercise = creative_service.creative_exercise("test_user")
        print(f"   {exercise[:100]}...\n")
        
        print("-" * 40)
        print()
    
    # Test creative history
    print("📚 Testing Creative History:")
    history = creative_service.get_creative_history("test_user", 10)
    print(f"   {history}")
    
    print("\n✅ Creative Expression system test completed successfully!")
    print("🚀 Ready to showcase Astra's personality-driven creativity!")

def test_personality_differences():
    """Test how different personalities create different content"""
    print("\n🎭 Testing Personality-Driven Creative Differences\n")
    
    topic = "dreams"
    
    modes = ['curious', 'creative', 'philosophical']
    
    for mode in modes:
        personality_service.switch_personality_mode(mode)
        poem = creative_service.create_poem(topic, f"test_{mode}")
        print(f"**{mode.title()} Mode Poem about '{topic}':**")
        print(poem)
        print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    test_creative_system()
    test_personality_differences()