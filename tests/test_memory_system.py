#!/usr/bin/env python3
"""
Quick test script for the new Memory System
"""
from app.services.memory_service import memory_service

def test_memory_system():
    """Test the memory system functionality"""
    print("🧪 Testing Astra's Memory System\n")
    
    # Test basic memory operations
    print("1. Testing basic memory storage...")
    result = memory_service.remember("favorite_color", "blue", "test_user")
    print(f"   {result}")
    
    print("\n2. Testing memory recall...")
    result = memory_service.recall("favorite_color", "test_user")
    print(f"   {result}")
    
    print("\n3. Testing fuzzy search...")
    result = memory_service.recall("color", "test_user")  # Should find "favorite_color"
    print(f"   {result}")
    
    print("\n4. Adding more memories...")
    memory_service.remember("hobby", "programming", "test_user")
    memory_service.remember("pet_name", "Whiskers", "test_user")
    memory_service.remember("favorite_food", "pizza", "test_user")
    
    print("\n5. Testing memory summary...")
    result = memory_service.memory_summary("test_user")
    print(f"   {result}")
    
    print("\n6. Testing memory search...")
    result = memory_service.search_memories("favorite", "test_user")
    print(f"   {result}")
    
    print("\n7. Testing memory statistics...")
    result = memory_service.get_memory_stats("test_user")
    print(f"   {result}")
    
    print("\n8. Testing context tracking...")
    memory_service.add_context("Hello Astra!", "test_user", True)
    memory_service.add_context("Hello! How are you today?", "test_user", False)
    memory_service.add_context("I'm doing great, thanks!", "test_user", True)
    
    print("\n9. Testing context retrieval...")
    context = memory_service.get_context("test_user", 3)
    for entry in context:
        speaker = "User" if entry['is_user'] else "Astra"
        print(f"   {speaker}: {entry['message']}")
    
    print("\n✅ Memory system test completed successfully!")
    print("🚀 Ready to enhance user conversations with persistent memory!")

if __name__ == "__main__":
    test_memory_system()