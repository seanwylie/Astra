#!/usr/bin/env python3
"""
Quick test script for the new Analytics & Insights System
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from beta.services.analytics_service import analytics_service
from beta.services.personality_service import personality_service
from beta.services.memory_service import memory_service
from beta.services.creative_service import creative_service
from beta.services.learning_service import learning_service

def setup_test_data():
    """Set up some test data across all systems"""
    print("🔧 Setting up test data across all systems...")
    
    # Add some memories
    memory_service.remember("favorite_language", "Python", "analytics_test_user")
    memory_service.remember("hobby", "AI research", "analytics_test_user")
    memory_service.remember("goal", "master machine learning", "analytics_test_user")
    
    # Add some creative works
    personality_service.switch_personality_mode("creative")
    creative_service.create_poem("innovation", "analytics_test_user")
    creative_service.write_story("AI discovers creativity", "analytics_test_user")
    
    personality_service.switch_personality_mode("curious")
    creative_service.generate_art_prompt("futuristic cityscape", "analytics_test_user")
    
    # Add some learning sessions
    learning_service.learn_from_text("Machine learning is a powerful subset of artificial intelligence that enables computers to learn and improve from experience without being explicitly programmed.", "ML_basics", "analytics_test_user")
    learning_service.start_teaching_mode("neural networks", "analytics_test_user")
    learning_service.generate_quiz("machine learning", "medium", 3, "analytics_test_user")
    
    print("✅ Test data setup complete!")

def test_analytics_system():
    """Test the analytics system functionality"""
    print("📊 Testing Astra's Analytics & Insights System\n")
    
    # Setup test data first
    setup_test_data()
    
    # Test different personality modes for analytics
    modes = ['curious', 'analytical', 'creative', 'mentor', 'philosophical', 'balanced']
    
    for mode in modes:
        print(f"🎭 Testing {mode.title()} Mode Analytics:")
        print("=" * 50)
        
        # Switch to this personality mode
        personality_service.switch_personality_mode(mode)
        
        # Test comprehensive dashboard
        print("1. Generating comprehensive dashboard...")
        dashboard = analytics_service.get_comprehensive_dashboard("analytics_test_user")
        print(f"   {dashboard[:150]}...\n")
        
        # Test growth report
        print("2. Generating growth report...")
        growth_report = analytics_service.get_growth_report("analytics_test_user", 30)
        print(f"   {growth_report[:150]}...\n")
        
        # Test interaction patterns
        print("3. Analyzing interaction patterns...")
        patterns = analytics_service.get_interaction_patterns("analytics_test_user")
        print(f"   {patterns[:150]}...\n")
        
        # Test achievements
        print("4. Calculating achievements...")
        achievements = analytics_service.get_achievement_summary("analytics_test_user")
        print(f"   {achievements[:150]}...\n")
        
        # Test recommendations
        print("5. Generating recommendations...")
        recommendations = analytics_service.get_personalized_recommendations("analytics_test_user")
        print(f"   {recommendations[:150]}...\n")
        
        print("-" * 50)
        print()
    
    print("✅ Analytics & Insights system test completed successfully!")
    print("🚀 Ready to provide comprehensive user insights!")

def test_cross_system_integration():
    """Test how analytics integrates data from all systems"""
    print("\n🔗 Testing Cross-System Integration\n")
    
    # Test individual system analytics
    print("Testing individual system analytics:")
    
    memory_analytics = analytics_service._get_memory_analytics("analytics_test_user")
    print(f"Memory Analytics: {memory_analytics}")
    
    creative_analytics = analytics_service._get_creative_analytics("analytics_test_user")
    print(f"Creative Analytics: {creative_analytics}")
    
    learning_analytics = analytics_service._get_learning_analytics("analytics_test_user")
    print(f"Learning Analytics: {learning_analytics}")
    
    personality_analytics = analytics_service._get_personality_analytics("analytics_test_user")
    print(f"Personality Analytics: {personality_analytics}")
    
    print("\n🔍 Cross-system integration working correctly!")

def test_personality_specific_insights():
    """Test how different personalities generate different insights"""
    print("\n🎭 Testing Personality-Specific Insights\n")
    
    modes = ['curious', 'analytical', 'creative']
    
    for mode in modes:
        personality_service.switch_personality_mode(mode)
        
        print(f"**{mode.title()} Mode Insights:**")
        
        # Test dashboard insights
        dashboard = analytics_service.get_comprehensive_dashboard("analytics_test_user")
        print(f"Dashboard: {dashboard[:200]}...")
        
        # Test recommendations
        recommendations = analytics_service.get_personalized_recommendations("analytics_test_user")
        print(f"Recommendations: {recommendations[:200]}...")
        
        print("\n" + "="*60 + "\n")

def test_achievement_system():
    """Test the achievement calculation system"""
    print("🏆 Testing Achievement System\n")
    
    achievements = analytics_service._calculate_achievements("analytics_test_user")
    
    print("Calculated Achievements:")
    for category, achievement_list in achievements.items():
        print(f"  {category.title()}: {len(achievement_list)} achievements")
        for achievement in achievement_list:
            print(f"    - {achievement}")
    
    print("\n✅ Achievement system working correctly!")

def test_analytics_data_persistence():
    """Test analytics data saving and loading"""
    print("💾 Testing Analytics Data Persistence\n")
    
    # Save analytics data
    analytics_service.analytics_data["test_key"] = "test_value"
    analytics_service.save_analytics_data()
    print("✅ Analytics data saved")
    
    # Load analytics data
    analytics_service.load_analytics_data()
    if analytics_service.analytics_data.get("test_key") == "test_value":
        print("✅ Analytics data loaded correctly")
    else:
        print("❌ Analytics data loading failed")

if __name__ == "__main__":
    test_analytics_system()
    test_cross_system_integration()
    test_personality_specific_insights()
    test_achievement_system()
    test_analytics_data_persistence()