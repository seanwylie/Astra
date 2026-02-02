#!/usr/bin/env python3
"""
Quick test script for the new Enhanced Learning Modes System
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.learning_service import learning_service
from app.services.personality_service import personality_service

def test_learning_system():
    """Test the learning system functionality"""
    print("🧠 Testing Astra's Enhanced Learning Modes System\n")
    
    # Test different personality modes
    modes = ['curious', 'analytical', 'creative', 'mentor', 'philosophical', 'balanced']
    
    for mode in modes:
        print(f"🎭 Testing {mode.title()} Mode:")
        print("=" * 40)
        
        # Switch to this personality mode
        personality_service.switch_personality_mode(mode)
        
        # Test learning from text
        print("1. Learning from text...")
        sample_text = f"Machine learning is a subset of artificial intelligence that focuses on algorithms that can learn from data. It involves training models on datasets to make predictions or decisions without being explicitly programmed for every scenario."
        result = learning_service.learn_from_text(sample_text, f"test_source_{mode}", "test_user")
        print(f"   {result[:100]}...\n")
        
        # Test teaching mode
        print("2. Starting teaching session...")
        teaching_result = learning_service.start_teaching_mode("artificial intelligence", "test_user")
        print(f"   {teaching_result[:100]}...\n")
        
        # Test quiz generation
        print("3. Generating quiz...")
        quiz_result = learning_service.generate_quiz("machine learning", "medium", 3, "test_user")
        print(f"   {quiz_result[:100]}...\n")
        
        # Test knowledge gap analysis
        print("4. Analyzing knowledge gaps...")
        gaps_result = learning_service.identify_knowledge_gaps("test_user")
        print(f"   {gaps_result[:100]}...\n")
        
        # Test study plan creation
        print("5. Creating study plan...")
        plan_result = learning_service.create_study_plan("master Python programming", "1 month", "test_user")
        print(f"   {plan_result[:100]}...\n")
        
        print("-" * 40)
        print()
    
    # Test learning statistics
    print("📊 Testing Learning Statistics:")
    stats = learning_service.get_learning_stats("test_user")
    print(f"   {stats}")
    
    print("\n✅ Enhanced Learning Modes system test completed successfully!")
    print("🚀 Ready to provide interactive learning experiences!")

def test_personality_learning_differences():
    """Test how different personalities approach learning"""
    print("\n🎭 Testing Personality-Driven Learning Differences\n")
    
    topic = "quantum computing"
    
    modes = ['curious', 'analytical', 'mentor']
    
    for mode in modes:
        personality_service.switch_personality_mode(mode)
        
        print(f"**{mode.title()} Mode Learning Approach:**")
        
        # Test learning response
        sample_content = "Quantum computing uses quantum mechanical phenomena like superposition and entanglement to process information in ways that classical computers cannot."
        result = learning_service.learn_from_text(sample_content, f"quantum_source", f"test_{mode}")
        print(f"Learning Response: {result[:150]}...")
        
        # Test teaching approach
        teaching = learning_service.start_teaching_mode(topic, f"test_{mode}")
        print(f"Teaching Approach: {teaching[:150]}...")
        
        print("\n" + "="*60 + "\n")

def test_knowledge_base_integration():
    """Test knowledge base building and retrieval"""
    print("🔍 Testing Knowledge Base Integration\n")
    
    # Add various learning content
    topics = [
        ("Python is a high-level programming language known for its simplicity and readability.", "python_basics"),
        ("Data structures organize and store data efficiently for various operations.", "data_structures"),
        ("Algorithms are step-by-step procedures for solving computational problems.", "algorithms")
    ]
    
    for content, source in topics:
        result = learning_service.learn_from_text(content, source, "knowledge_test_user")
        print(f"Added: {source}")
    
    # Test knowledge retrieval and connections
    print("\nKnowledge Base Contents:")
    for concept, entries in learning_service.knowledge_base.items():
        print(f"• {concept}: {len(entries)} entries")
    
    # Test gap analysis with built knowledge
    gaps = learning_service.identify_knowledge_gaps("knowledge_test_user")
    print(f"\nGap Analysis:\n{gaps}")

if __name__ == "__main__":
    test_learning_system()
    test_personality_learning_differences()
    test_knowledge_base_integration()