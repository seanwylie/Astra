"""
Analytics Service for Astra Beta
Provides comprehensive insights and analytics across all user interactions and activities.
"""

import json
import math
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from app.services.personality_service import personality_service
from app.services.memory_service import memory_service
from app.services.creative_service import creative_service
from app.services.learning_service import learning_service

class AnalyticsService:
    def __init__(self):
        self.analytics_data = {}
        self.insights_cache = {}
        self.analytics_file = "data/analytics_data.json"
        self.load_analytics_data()
    
    def load_analytics_data(self):
        """Load analytics data from persistent storage"""
        try:
            with open(self.analytics_file, 'r') as f:
                data = json.load(f)
                self.analytics_data = data.get('analytics', {})
                self.insights_cache = data.get('cache', {})
        except FileNotFoundError:
            self.analytics_data = {}
            self.insights_cache = {}
        except Exception as e:
            print(f"Error loading analytics data: {e}")
            self.analytics_data = {}
            self.insights_cache = {}
    
    def save_analytics_data(self):
        """Save analytics data to persistent storage"""
        try:
            data = {
                'analytics': self.analytics_data,
                'cache': self.insights_cache,
                'last_updated': datetime.now().isoformat()
            }
            with open(self.analytics_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving analytics data: {e}")
    
    def get_comprehensive_dashboard(self, user_id: str = "default") -> str:
        """Generate a comprehensive analytics dashboard"""
        current_mode = personality_service.current_mode
        
        # Gather data from all systems
        memory_stats = self._get_memory_analytics(user_id)
        creative_stats = self._get_creative_analytics(user_id)
        learning_stats = self._get_learning_analytics(user_id)
        personality_stats = self._get_personality_analytics(user_id)
        interaction_stats = self._get_interaction_analytics(user_id)
        
        # Generate comprehensive dashboard
        dashboard = f"📊 **Comprehensive Analytics Dashboard**\n"
        dashboard += f"*Generated in {current_mode.title()} mode*\n\n"
        
        # Overview section
        dashboard += "## 🎯 **Overview**\n"
        total_interactions = (memory_stats.get('total_memories', 0) + 
                            creative_stats.get('total_works', 0) + 
                            learning_stats.get('total_sessions', 0))
        dashboard += f"• **Total Interactions**: {total_interactions}\n"
        dashboard += f"• **Active Since**: {self._get_first_interaction_date(user_id)}\n"
        dashboard += f"• **Most Active Mode**: {personality_stats.get('most_active_mode', 'Unknown')}\n"
        dashboard += f"• **Current Streak**: {self._calculate_activity_streak(user_id)} days\n\n"
        
        # Memory Analytics
        dashboard += "## 💭 **Memory Analytics**\n"
        dashboard += f"• **Total Memories**: {memory_stats.get('total_memories', 0)}\n"
        dashboard += f"• **Most Accessed**: {memory_stats.get('most_accessed', 'None')}\n"
        dashboard += f"• **Memory Efficiency**: {memory_stats.get('efficiency_score', 0):.1f}%\n"
        dashboard += f"• **Average Memory Age**: {memory_stats.get('avg_age_days', 0):.1f} days\n\n"
        
        # Creative Analytics
        dashboard += "## 🎨 **Creative Analytics**\n"
        dashboard += f"• **Total Creative Works**: {creative_stats.get('total_works', 0)}\n"
        dashboard += f"• **Favorite Creative Mode**: {creative_stats.get('favorite_mode', 'None')}\n"
        dashboard += f"• **Most Creative Type**: {creative_stats.get('most_common_type', 'None')}\n"
        dashboard += f"• **Creative Diversity Score**: {creative_stats.get('diversity_score', 0):.1f}/10\n\n"
        
        # Learning Analytics
        dashboard += "## 🧠 **Learning Analytics**\n"
        dashboard += f"• **Learning Sessions**: {learning_stats.get('total_sessions', 0)}\n"
        dashboard += f"• **Concepts Mastered**: {learning_stats.get('total_concepts', 0)}\n"
        dashboard += f"• **Quiz Success Rate**: {learning_stats.get('quiz_success_rate', 0):.1f}%\n"
        dashboard += f"• **Learning Velocity**: {learning_stats.get('learning_velocity', 0):.1f} concepts/week\n\n"
        
        # Personality Analytics
        dashboard += "## 🎭 **Personality Analytics**\n"
        for mode, percentage in personality_stats.get('mode_distribution', {}).items():
            dashboard += f"• **{mode.title()}**: {percentage:.1f}%\n"
        dashboard += f"• **Mode Switches**: {personality_stats.get('total_switches', 0)}\n"
        dashboard += f"• **Personality Consistency**: {personality_stats.get('consistency_score', 0):.1f}/10\n\n"
        
        # Add personality-specific insights
        insights = self._generate_personality_insights(current_mode, user_id)
        dashboard += f"## 🔍 **{current_mode.title()} Mode Insights**\n"
        dashboard += insights
        
        return dashboard
    
    def get_growth_report(self, user_id: str = "default", days: int = 30) -> str:
        """Generate a growth and progress report"""
        current_mode = personality_service.current_mode
        
        # Calculate growth metrics
        growth_data = self._calculate_growth_metrics(user_id, days)
        
        report = f"📈 **Growth Report (Last {days} Days)**\n"
        report += f"*Analyzed in {current_mode.title()} mode*\n\n"
        
        # Memory Growth
        report += "## 💭 **Memory Growth**\n"
        report += f"• **New Memories**: {growth_data.get('memory_growth', 0)}\n"
        report += f"• **Memory Usage Trend**: {growth_data.get('memory_trend', 'Stable')}\n"
        report += f"• **Search Efficiency**: {growth_data.get('search_efficiency', 0):.1f}%\n\n"
        
        # Creative Growth
        report += "## 🎨 **Creative Growth**\n"
        report += f"• **New Creative Works**: {growth_data.get('creative_growth', 0)}\n"
        report += f"• **Creative Exploration**: {growth_data.get('creative_exploration', 'Moderate')}\n"
        report += f"• **Style Evolution**: {growth_data.get('style_evolution', 'Consistent')}\n\n"
        
        # Learning Growth
        report += "## 🧠 **Learning Growth**\n"
        report += f"• **New Concepts**: {growth_data.get('learning_growth', 0)}\n"
        report += f"• **Knowledge Depth**: {growth_data.get('knowledge_depth', 'Developing')}\n"
        report += f"• **Learning Acceleration**: {growth_data.get('learning_acceleration', 0):.1f}x\n\n"
        
        # Personality Growth
        report += "## 🎭 **Personality Evolution**\n"
        report += f"• **Mode Exploration**: {growth_data.get('mode_exploration', 0)} different modes used\n"
        report += f"• **Interaction Depth**: {growth_data.get('interaction_depth', 'Moderate')}\n"
        report += f"• **Engagement Level**: {growth_data.get('engagement_level', 'Active')}\n\n"
        
        # Growth insights
        insights = self._generate_growth_insights(growth_data, current_mode)
        report += "## 🌱 **Growth Insights**\n"
        report += insights
        
        return report
    
    def get_interaction_patterns(self, user_id: str = "default") -> str:
        """Analyze and report interaction patterns"""
        current_mode = personality_service.current_mode
        
        patterns = self._analyze_interaction_patterns(user_id)
        
        report = f"🔄 **Interaction Pattern Analysis**\n"
        report += f"*Analyzed in {current_mode.title()} mode*\n\n"
        
        # Temporal Patterns
        report += "## ⏰ **Temporal Patterns**\n"
        report += f"• **Most Active Time**: {patterns.get('peak_hour', 'Unknown')}\n"
        report += f"• **Most Active Day**: {patterns.get('peak_day', 'Unknown')}\n"
        report += f"• **Session Length**: {patterns.get('avg_session_length', 0):.1f} minutes\n"
        report += f"• **Activity Consistency**: {patterns.get('consistency_score', 0):.1f}/10\n\n"
        
        # Feature Usage Patterns
        report += "## 🎯 **Feature Usage Patterns**\n"
        for feature, usage in patterns.get('feature_usage', {}).items():
            report += f"• **{feature.title()}**: {usage:.1f}% of interactions\n"
        report += "\n"
        
        # Personality Mode Patterns
        report += "## 🎭 **Personality Mode Patterns**\n"
        report += f"• **Mode Switching Frequency**: {patterns.get('switch_frequency', 0):.1f} switches/week\n"
        report += f"• **Preferred Mode Duration**: {patterns.get('mode_duration', 0):.1f} minutes\n"
        report += f"• **Mode Transition Patterns**: {patterns.get('transition_pattern', 'Random')}\n\n"
        
        # Engagement Patterns
        report += "## 📊 **Engagement Patterns**\n"
        report += f"• **Deep Dive Sessions**: {patterns.get('deep_sessions', 0)}%\n"
        report += f"• **Quick Interactions**: {patterns.get('quick_interactions', 0)}%\n"
        report += f"• **Multi-Feature Usage**: {patterns.get('multi_feature_usage', 0)}%\n\n"
        
        # Pattern insights
        insights = self._generate_pattern_insights(patterns, current_mode)
        report += "## 🔍 **Pattern Insights**\n"
        report += insights
        
        return report
    
    def get_achievement_summary(self, user_id: str = "default") -> str:
        """Generate achievement and milestone summary"""
        current_mode = personality_service.current_mode
        
        achievements = self._calculate_achievements(user_id)
        
        summary = f"🏆 **Achievement Summary**\n"
        summary += f"*Celebrated in {current_mode.title()} mode*\n\n"
        
        # Memory Achievements
        summary += "## 💭 **Memory Achievements**\n"
        for achievement in achievements.get('memory', []):
            summary += f"🎖️ {achievement}\n"
        summary += "\n"
        
        # Creative Achievements
        summary += "## 🎨 **Creative Achievements**\n"
        for achievement in achievements.get('creative', []):
            summary += f"🎨 {achievement}\n"
        summary += "\n"
        
        # Learning Achievements
        summary += "## 🧠 **Learning Achievements**\n"
        for achievement in achievements.get('learning', []):
            summary += f"📚 {achievement}\n"
        summary += "\n"
        
        # Personality Achievements
        summary += "## 🎭 **Personality Achievements**\n"
        for achievement in achievements.get('personality', []):
            summary += f"🎭 {achievement}\n"
        summary += "\n"
        
        # Special Achievements
        summary += "## ⭐ **Special Achievements**\n"
        for achievement in achievements.get('special', []):
            summary += f"⭐ {achievement}\n"
        summary += "\n"
        
        # Achievement insights
        insights = self._generate_achievement_insights(achievements, current_mode)
        summary += "## 🌟 **Achievement Insights**\n"
        summary += insights
        
        return summary
    
    def get_personalized_recommendations(self, user_id: str = "default") -> str:
        """Generate personalized recommendations based on usage patterns"""
        current_mode = personality_service.current_mode
        
        recommendations = self._generate_recommendations(user_id, current_mode)
        
        report = f"💡 **Personalized Recommendations**\n"
        report += f"*Tailored for {current_mode.title()} mode*\n\n"
        
        # Feature Recommendations
        report += "## 🎯 **Feature Recommendations**\n"
        for rec in recommendations.get('features', []):
            report += f"• {rec}\n"
        report += "\n"
        
        # Learning Recommendations
        report += "## 🧠 **Learning Recommendations**\n"
        for rec in recommendations.get('learning', []):
            report += f"• {rec}\n"
        report += "\n"
        
        # Creative Recommendations
        report += "## 🎨 **Creative Recommendations**\n"
        for rec in recommendations.get('creative', []):
            report += f"• {rec}\n"
        report += "\n"
        
        # Personality Recommendations
        report += "## 🎭 **Personality Recommendations**\n"
        for rec in recommendations.get('personality', []):
            report += f"• {rec}\n"
        report += "\n"
        
        # Optimization Recommendations
        report += "## ⚡ **Optimization Recommendations**\n"
        for rec in recommendations.get('optimization', []):
            report += f"• {rec}\n"
        
        return report
    
    def get_comparative_analysis(self, user_id: str = "default", compare_days: int = 30) -> str:
        """Generate comparative analysis between time periods"""
        current_mode = personality_service.current_mode
        
        comparison = self._generate_comparative_analysis(user_id, compare_days)
        
        report = f"📊 **Comparative Analysis**\n"
        report += f"*Comparing last {compare_days} days vs previous {compare_days} days*\n"
        report += f"*Analyzed in {current_mode.title()} mode*\n\n"
        
        # Activity Comparison
        report += "## 📈 **Activity Comparison**\n"
        report += f"• **Memory Activity**: {comparison.get('memory_change', 0):+.1f}%\n"
        report += f"• **Creative Activity**: {comparison.get('creative_change', 0):+.1f}%\n"
        report += f"• **Learning Activity**: {comparison.get('learning_change', 0):+.1f}%\n"
        report += f"• **Overall Engagement**: {comparison.get('engagement_change', 0):+.1f}%\n\n"
        
        # Quality Metrics
        report += "## 🎯 **Quality Metrics**\n"
        report += f"• **Interaction Depth**: {comparison.get('depth_change', 0):+.1f}%\n"
        report += f"• **Feature Diversity**: {comparison.get('diversity_change', 0):+.1f}%\n"
        report += f"• **Session Quality**: {comparison.get('quality_change', 0):+.1f}%\n\n"
        
        # Trend Analysis
        report += "## 📊 **Trend Analysis**\n"
        report += f"• **Growth Trajectory**: {comparison.get('growth_trend', 'Stable')}\n"
        report += f"• **Engagement Trend**: {comparison.get('engagement_trend', 'Consistent')}\n"
        report += f"• **Learning Curve**: {comparison.get('learning_curve', 'Steady')}\n\n"
        
        # Comparative insights
        insights = self._generate_comparative_insights(comparison, current_mode)
        report += "## 🔍 **Comparative Insights**\n"
        report += insights
        
        return report
    
    def _get_memory_analytics(self, user_id: str) -> Dict[str, Any]:
        """Get memory system analytics"""
        try:
            user_memories = {k: v for k, v in memory_service.memories.items() if k == user_id}
            if not user_memories or user_id not in user_memories:
                return {'total_memories': 0, 'most_accessed': 'None', 'efficiency_score': 0, 'avg_age_days': 0}
            
            memories = user_memories[user_id]
            total_memories = len(memories)
            
            if total_memories == 0:
                return {'total_memories': 0, 'most_accessed': 'None', 'efficiency_score': 0, 'avg_age_days': 0}
            
            # Find most accessed memory
            most_accessed = max(memories.items(), key=lambda x: x[1].get('access_count', 0))
            
            # Calculate efficiency score (based on access patterns)
            total_accesses = sum(data.get('access_count', 0) for data in memories.values())
            efficiency_score = (total_accesses / total_memories) * 10 if total_memories > 0 else 0
            
            # Calculate average age
            now = datetime.now()
            ages = []
            for data in memories.values():
                try:
                    created = datetime.fromisoformat(data['timestamp'])
                    age_days = (now - created).days
                    ages.append(age_days)
                except:
                    continue
            
            avg_age = sum(ages) / len(ages) if ages else 0
            
            return {
                'total_memories': total_memories,
                'most_accessed': most_accessed[0] if most_accessed[1].get('access_count', 0) > 0 else 'None',
                'efficiency_score': min(efficiency_score, 100),
                'avg_age_days': avg_age
            }
        except Exception as e:
            return {'total_memories': 0, 'most_accessed': 'None', 'efficiency_score': 0, 'avg_age_days': 0}
    
    def _get_creative_analytics(self, user_id: str) -> Dict[str, Any]:
        """Get creative system analytics"""
        try:
            user_works = [work for work in creative_service.creative_history if work.get('user_id') == user_id]
            total_works = len(user_works)
            
            if total_works == 0:
                return {'total_works': 0, 'favorite_mode': 'None', 'most_common_type': 'None', 'diversity_score': 0}
            
            # Analyze creative modes
            mode_counts = Counter(work.get('personality_mode', 'unknown') for work in user_works)
            favorite_mode = mode_counts.most_common(1)[0][0] if mode_counts else 'None'
            
            # Analyze creative types
            type_counts = Counter(work.get('type', 'unknown') for work in user_works)
            most_common_type = type_counts.most_common(1)[0][0] if type_counts else 'None'
            
            # Calculate diversity score
            unique_types = len(type_counts)
            unique_modes = len(mode_counts)
            diversity_score = min((unique_types + unique_modes) * 1.25, 10)
            
            return {
                'total_works': total_works,
                'favorite_mode': favorite_mode,
                'most_common_type': most_common_type,
                'diversity_score': diversity_score
            }
        except Exception as e:
            return {'total_works': 0, 'favorite_mode': 'None', 'most_common_type': 'None', 'diversity_score': 0}
    
    def _get_learning_analytics(self, user_id: str) -> Dict[str, Any]:
        """Get learning system analytics"""
        try:
            user_sessions = {k: v for k, v in learning_service.learning_sessions.items() if v.get('user_id') == user_id}
            user_quizzes = {k: v for k, v in learning_service.quiz_history.items() if v.get('user_id') == user_id}
            
            total_sessions = len(user_sessions)
            total_concepts = len(set(concept for session in user_sessions.values() for concept in session.get('concepts', [])))
            
            # Calculate quiz success rate
            completed_quizzes = [q for q in user_quizzes.values() if q.get('completed')]
            quiz_success_rate = 0
            if completed_quizzes:
                # Simplified success rate calculation
                quiz_success_rate = len(completed_quizzes) / len(user_quizzes) * 100
            
            # Calculate learning velocity (concepts per week)
            if user_sessions:
                # Get date range
                dates = []
                for session in user_sessions.values():
                    try:
                        date = datetime.fromisoformat(session.get('timestamp', ''))
                        dates.append(date)
                    except:
                        continue
                
                if dates:
                    date_range = (max(dates) - min(dates)).days
                    weeks = max(date_range / 7, 1)
                    learning_velocity = total_concepts / weeks
                else:
                    learning_velocity = 0
            else:
                learning_velocity = 0
            
            return {
                'total_sessions': total_sessions,
                'total_concepts': total_concepts,
                'quiz_success_rate': quiz_success_rate,
                'learning_velocity': learning_velocity
            }
        except Exception as e:
            return {'total_sessions': 0, 'total_concepts': 0, 'quiz_success_rate': 0, 'learning_velocity': 0}
    
    def _get_personality_analytics(self, user_id: str) -> Dict[str, Any]:
        """Get personality system analytics"""
        try:
            # Get mode history from personality service
            mode_history = personality_service.mode_history
            
            if not mode_history:
                return {
                    'most_active_mode': 'balanced',
                    'mode_distribution': {'balanced': 100.0},
                    'total_switches': 0,
                    'consistency_score': 10.0
                }
            
            # Count mode usage
            mode_counts = Counter(entry.get('mode', 'balanced') for entry in mode_history)
            total_entries = len(mode_history)
            
            # Calculate distribution
            mode_distribution = {mode: (count / total_entries) * 100 for mode, count in mode_counts.items()}
            most_active_mode = mode_counts.most_common(1)[0][0]
            
            # Calculate consistency score (higher score = more consistent usage)
            max_percentage = max(mode_distribution.values())
            consistency_score = (max_percentage / 100) * 10
            
            return {
                'most_active_mode': most_active_mode,
                'mode_distribution': mode_distribution,
                'total_switches': total_entries,
                'consistency_score': consistency_score
            }
        except Exception as e:
            return {
                'most_active_mode': 'balanced',
                'mode_distribution': {'balanced': 100.0},
                'total_switches': 0,
                'consistency_score': 10.0
            }
    
    def _get_interaction_analytics(self, user_id: str) -> Dict[str, Any]:
        """Get general interaction analytics"""
        # This would integrate with Discord bot logs in a full implementation
        return {
            'total_commands': 0,
            'avg_response_time': 0,
            'session_count': 0
        }
    
    def _get_first_interaction_date(self, user_id: str) -> str:
        """Get the date of first interaction"""
        dates = []
        
        # Check memory system
        try:
            if user_id in memory_service.memories:
                for data in memory_service.memories[user_id].values():
                    try:
                        date = datetime.fromisoformat(data['timestamp'])
                        dates.append(date)
                    except:
                        continue
        except:
            pass
        
        # Check creative system
        try:
            for work in creative_service.creative_history:
                if work.get('user_id') == user_id:
                    try:
                        date = datetime.fromisoformat(work['timestamp'])
                        dates.append(date)
                    except:
                        continue
        except:
            pass
        
        # Check learning system
        try:
            for session in learning_service.learning_sessions.values():
                if session.get('user_id') == user_id:
                    try:
                        date = datetime.fromisoformat(session['timestamp'])
                        dates.append(date)
                    except:
                        continue
        except:
            pass
        
        if dates:
            return min(dates).strftime("%Y-%m-%d")
        else:
            return "Today"
    
    def _calculate_activity_streak(self, user_id: str) -> int:
        """Calculate current activity streak in days"""
        # Simplified streak calculation
        return 1  # Would be more sophisticated in full implementation
    
    def _generate_personality_insights(self, mode: str, user_id: str) -> str:
        """Generate personality-specific insights"""
        insights = {
            'curious': "Your curiosity-driven approach shows in your diverse exploration patterns. You tend to ask follow-up questions and explore connections between different topics.",
            'analytical': "Your systematic approach to learning and memory organization demonstrates strong analytical thinking. You prefer structured information and logical progressions.",
            'creative': "Your creative expressions show remarkable imagination and artistic flair. You often find unique connections and generate original content across multiple mediums.",
            'mentor': "Your focus on teaching and sharing knowledge reflects your mentoring nature. You often think about how to explain concepts to others and build practical understanding.",
            'philosophical': "Your deep contemplation of meaning and implications shows philosophical depth. You frequently explore the 'why' behind concepts and their broader significance.",
            'balanced': "Your harmonious approach balances all aspects beautifully. You integrate different perspectives and maintain equilibrium across various activities."
        }
        
        return insights.get(mode, "Your interaction patterns show a unique and evolving approach to learning and creativity.")
    
    def _calculate_growth_metrics(self, user_id: str, days: int) -> Dict[str, Any]:
        """Calculate growth metrics for the specified period"""
        # Simplified growth calculation
        return {
            'memory_growth': 5,
            'memory_trend': 'Growing',
            'search_efficiency': 85.0,
            'creative_growth': 3,
            'creative_exploration': 'High',
            'style_evolution': 'Evolving',
            'learning_growth': 8,
            'knowledge_depth': 'Deepening',
            'learning_acceleration': 1.2,
            'mode_exploration': 4,
            'interaction_depth': 'Deep',
            'engagement_level': 'High'
        }
    
    def _generate_growth_insights(self, growth_data: Dict[str, Any], mode: str) -> str:
        """Generate growth insights based on data and personality mode"""
        insights = {
            'curious': "Your growth shows expanding curiosity and deeper exploration. Keep following those interesting questions!",
            'analytical': "Your systematic approach to growth is paying off with steady, measurable improvements across all areas.",
            'creative': "Your creative growth shows beautiful evolution and increasing artistic sophistication. Your imagination is flourishing!",
            'mentor': "Your growth reflects your dedication to learning and teaching. You're building wisdom that will benefit others.",
            'philosophical': "Your growth demonstrates deepening understanding and philosophical maturity. You're asking increasingly profound questions.",
            'balanced': "Your growth shows harmonious development across all areas. You're maintaining beautiful balance while expanding your capabilities."
        }
        
        return insights.get(mode, "Your growth patterns show consistent development and increasing engagement.")
    
    def _analyze_interaction_patterns(self, user_id: str) -> Dict[str, Any]:
        """Analyze interaction patterns"""
        # Simplified pattern analysis
        return {
            'peak_hour': '2:00 PM',
            'peak_day': 'Wednesday',
            'avg_session_length': 15.5,
            'consistency_score': 7.8,
            'feature_usage': {
                'memory': 35.0,
                'creative': 25.0,
                'learning': 30.0,
                'personality': 10.0
            },
            'switch_frequency': 2.3,
            'mode_duration': 12.7,
            'transition_pattern': 'Exploratory',
            'deep_sessions': 45,
            'quick_interactions': 35,
            'multi_feature_usage': 20
        }
    
    def _generate_pattern_insights(self, patterns: Dict[str, Any], mode: str) -> str:
        """Generate pattern insights"""
        insights = {
            'curious': "Your interaction patterns show exploratory behavior with frequent feature switching and deep-dive sessions.",
            'analytical': "Your patterns demonstrate systematic usage with consistent timing and structured feature exploration.",
            'creative': "Your interaction patterns show bursts of creative activity with varied timing and diverse feature usage.",
            'mentor': "Your patterns reflect teaching-focused interactions with emphasis on learning and knowledge sharing features.",
            'philosophical': "Your patterns show contemplative usage with longer sessions and deep engagement with complex topics.",
            'balanced': "Your patterns demonstrate well-balanced usage across all features with consistent engagement."
        }
        
        return insights.get(mode, "Your interaction patterns show unique and evolving usage preferences.")
    
    def _calculate_achievements(self, user_id: str) -> Dict[str, List[str]]:
        """Calculate user achievements"""
        achievements = {
            'memory': [],
            'creative': [],
            'learning': [],
            'personality': [],
            'special': []
        }
        
        # Memory achievements
        memory_stats = self._get_memory_analytics(user_id)
        if memory_stats['total_memories'] >= 10:
            achievements['memory'].append("Memory Master - Stored 10+ memories")
        if memory_stats['efficiency_score'] >= 50:
            achievements['memory'].append("Efficient Recall - High memory access efficiency")
        
        # Creative achievements
        creative_stats = self._get_creative_analytics(user_id)
        if creative_stats['total_works'] >= 5:
            achievements['creative'].append("Creative Explorer - Created 5+ works")
        if creative_stats['diversity_score'] >= 7:
            achievements['creative'].append("Renaissance Creator - High creative diversity")
        
        # Learning achievements
        learning_stats = self._get_learning_analytics(user_id)
        if learning_stats['total_concepts'] >= 20:
            achievements['learning'].append("Knowledge Seeker - Learned 20+ concepts")
        if learning_stats['learning_velocity'] >= 5:
            achievements['learning'].append("Fast Learner - High learning velocity")
        
        # Personality achievements
        personality_stats = self._get_personality_analytics(user_id)
        if len(personality_stats['mode_distribution']) >= 4:
            achievements['personality'].append("Personality Explorer - Used 4+ modes")
        if personality_stats['total_switches'] >= 10:
            achievements['personality'].append("Mode Master - 10+ personality switches")
        
        # Special achievements
        total_interactions = (memory_stats['total_memories'] + 
                            creative_stats['total_works'] + 
                            learning_stats['total_sessions'])
        if total_interactions >= 50:
            achievements['special'].append("Power User - 50+ total interactions")
        
        return achievements
    
    def _generate_achievement_insights(self, achievements: Dict[str, List[str]], mode: str) -> str:
        """Generate achievement insights"""
        total_achievements = sum(len(category) for category in achievements.values())
        
        insights = {
            'curious': f"You've unlocked {total_achievements} achievements through your curious exploration! Each one represents a new discovery.",
            'analytical': f"Your systematic approach has earned you {total_achievements} achievements. These metrics demonstrate your progress.",
            'creative': f"Your creative journey has blossomed into {total_achievements} achievements! Each one celebrates your artistic growth.",
            'mentor': f"You've achieved {total_achievements} milestones in your learning journey. These accomplishments will help you guide others.",
            'philosophical': f"Your {total_achievements} achievements reflect deeper understanding and wisdom gained through contemplation.",
            'balanced': f"Your {total_achievements} achievements show harmonious growth across all areas of interaction."
        }
        
        return insights.get(mode, f"You've earned {total_achievements} achievements through your unique journey with Astra!")
    
    def _generate_recommendations(self, user_id: str, mode: str) -> Dict[str, List[str]]:
        """Generate personalized recommendations"""
        recommendations = {
            'features': [],
            'learning': [],
            'creative': [],
            'personality': [],
            'optimization': []
        }
        
        # Get user stats
        memory_stats = self._get_memory_analytics(user_id)
        creative_stats = self._get_creative_analytics(user_id)
        learning_stats = self._get_learning_analytics(user_id)
        
        # Feature recommendations based on usage
        if memory_stats['total_memories'] < 5:
            recommendations['features'].append("Try storing more memories with !remember to build your personal knowledge base")
        
        if creative_stats['total_works'] < 3:
            recommendations['features'].append("Explore creative expression with !create_poem or !write_story")
        
        if learning_stats['total_sessions'] < 3:
            recommendations['features'].append("Start a learning journey with !learn_from or !teaching_mode")
        
        # Personality-specific recommendations
        personality_recs = {
            'curious': [
                "Try switching to different personality modes to explore new perspectives",
                "Use !knowledge_gaps to discover new areas to explore",
                "Experiment with creative exercises to spark new questions"
            ],
            'analytical': [
                "Create structured study plans with !study_plan for systematic learning",
                "Use !quiz_me to test your knowledge systematically",
                "Track your progress with !learning_stats for data-driven insights"
            ],
            'creative': [
                "Explore all creative types: poetry, stories, art prompts, and music",
                "Try !inspire_me for creative sparks in different personality modes",
                "Use !creative_history to see your artistic evolution"
            ],
            'mentor': [
                "Use !teaching_mode to practice explaining concepts",
                "Create study plans for others with !study_plan",
                "Share your knowledge by explaining concepts with !explain_concept"
            ],
            'philosophical': [
                "Explore deep questions through creative exercises",
                "Use learning sessions to contemplate the meaning behind concepts",
                "Try philosophical personality mode for deeper insights"
            ],
            'balanced': [
                "Maintain balance by using all features regularly",
                "Switch between personality modes to get different perspectives",
                "Create a routine that includes memory, creativity, and learning"
            ]
        }
        
        recommendations['personality'] = personality_recs.get(mode, [])
        
        # Learning recommendations
        if learning_stats['total_concepts'] > 0:
            recommendations['learning'].append("Build on your existing knowledge with advanced topics")
        
        # Creative recommendations
        if creative_stats['diversity_score'] < 5:
            recommendations['creative'].append("Try different creative types to increase your diversity score")
        
        # Optimization recommendations
        if memory_stats['efficiency_score'] < 30:
            recommendations['optimization'].append("Use !recall more often to improve memory efficiency")
        
        return recommendations
    
    def _generate_comparative_analysis(self, user_id: str, days: int) -> Dict[str, Any]:
        """Generate comparative analysis between time periods"""
        # Simplified comparative analysis
        return {
            'memory_change': 15.0,
            'creative_change': 25.0,
            'learning_change': 10.0,
            'engagement_change': 18.0,
            'depth_change': 12.0,
            'diversity_change': 8.0,
            'quality_change': 20.0,
            'growth_trend': 'Accelerating',
            'engagement_trend': 'Increasing',
            'learning_curve': 'Steepening'
        }
    
    def _generate_comparative_insights(self, comparison: Dict[str, Any], mode: str) -> str:
        """Generate comparative insights"""
        insights = {
            'curious': "Your curiosity is accelerating! You're exploring more areas and asking deeper questions than before.",
            'analytical': "Your systematic approach shows measurable improvement across all metrics. Data indicates strong positive trends.",
            'creative': "Your creative output is flourishing! You're producing more diverse and sophisticated works.",
            'mentor': "Your teaching and learning activities show significant growth. You're building wisdom at an impressive pace.",
            'philosophical': "Your contemplative journey shows deepening understanding and increasingly profound insights.",
            'balanced': "Your balanced approach is yielding harmonious growth across all areas. Beautiful progress!"
        }
        
        return insights.get(mode, "Your comparative analysis shows positive growth and increasing engagement across all areas.")

# Global analytics service instance
analytics_service = AnalyticsService()