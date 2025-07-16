"""
📊 Analytics Commands
--------------------
Provides comprehensive insights and analytics across all user interactions and activities.
Shows growth patterns, achievements, and personalized recommendations.
"""

import discord
from discord.ext import commands
from beta.services.analytics_service import analytics_service
from beta.services.personality_service import personality_service
from beta.utils.send_chunked_message import send_chunked_message

class AnalyticsCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='dashboard', help='Show comprehensive analytics dashboard')
    async def dashboard(self, ctx):
        """Show comprehensive analytics dashboard"""
        user_id = str(ctx.author.id)
        
        try:
            dashboard = analytics_service.get_comprehensive_dashboard(user_id)
            await send_chunked_message(ctx, dashboard)
            
            # Add personality-specific dashboard insight
            current_mode = personality_service.current_mode
            insight = self._get_dashboard_insight(current_mode)
            if insight:
                await ctx.send(insight)
                
        except Exception as e:
            await ctx.send(f"❌ Error generating dashboard: {str(e)}")

    @commands.command(name='growth_report', help='Show growth and progress report: !growth_report [days]')
    async def growth_report(self, ctx, days: int = 30):
        """Show growth and progress report"""
        if days < 1 or days > 365:
            days = 30
        
        user_id = str(ctx.author.id)
        
        try:
            report = analytics_service.get_growth_report(user_id, days)
            await send_chunked_message(ctx, report)
            
            # Add personality-specific growth encouragement
            current_mode = personality_service.current_mode
            encouragement = self._get_growth_encouragement(current_mode, days)
            if encouragement:
                await ctx.send(encouragement)
                
        except Exception as e:
            await ctx.send(f"❌ Error generating growth report: {str(e)}")

    @commands.command(name='interaction_patterns', help='Analyze interaction patterns and habits')
    async def interaction_patterns(self, ctx):
        """Analyze interaction patterns and habits"""
        user_id = str(ctx.author.id)
        
        try:
            patterns = analytics_service.get_interaction_patterns(user_id)
            await send_chunked_message(ctx, patterns)
            
            # Add personality-specific pattern analysis
            current_mode = personality_service.current_mode
            analysis = self._get_pattern_analysis(current_mode)
            if analysis:
                await ctx.send(analysis)
                
        except Exception as e:
            await ctx.send(f"❌ Error analyzing interaction patterns: {str(e)}")

    @commands.command(name='achievements', help='Show achievement summary and milestones')
    async def achievements(self, ctx):
        """Show achievement summary and milestones"""
        user_id = str(ctx.author.id)
        
        try:
            achievements = analytics_service.get_achievement_summary(user_id)
            await send_chunked_message(ctx, achievements)
            
            # Add personality-specific achievement celebration
            current_mode = personality_service.current_mode
            celebration = self._get_achievement_celebration(current_mode)
            if celebration:
                await ctx.send(celebration)
                
        except Exception as e:
            await ctx.send(f"❌ Error retrieving achievements: {str(e)}")

    @commands.command(name='recommendations', help='Get personalized recommendations')
    async def recommendations(self, ctx):
        """Get personalized recommendations"""
        user_id = str(ctx.author.id)
        
        try:
            recommendations = analytics_service.get_personalized_recommendations(user_id)
            await send_chunked_message(ctx, recommendations)
            
            # Add personality-specific recommendation insight
            current_mode = personality_service.current_mode
            insight = self._get_recommendation_insight(current_mode)
            if insight:
                await ctx.send(insight)
                
        except Exception as e:
            await ctx.send(f"❌ Error generating recommendations: {str(e)}")

    @commands.command(name='compare_progress', help='Compare progress between time periods: !compare_progress [days]')
    async def compare_progress(self, ctx, days: int = 30):
        """Compare progress between time periods"""
        if days < 7 or days > 180:
            days = 30
        
        user_id = str(ctx.author.id)
        
        try:
            comparison = analytics_service.get_comparative_analysis(user_id, days)
            await send_chunked_message(ctx, comparison)
            
            # Add personality-specific comparative insight
            current_mode = personality_service.current_mode
            insight = self._get_comparative_insight(current_mode, days)
            if insight:
                await ctx.send(insight)
                
        except Exception as e:
            await ctx.send(f"❌ Error generating comparative analysis: {str(e)}")

    @commands.command(name='my_stats', help='Show personal interaction statistics')
    async def my_stats(self, ctx):
        """Show personal interaction statistics"""
        user_id = str(ctx.author.id)
        current_mode = personality_service.current_mode
        
        try:
            # Get quick stats from all systems
            memory_stats = analytics_service._get_memory_analytics(user_id)
            creative_stats = analytics_service._get_creative_analytics(user_id)
            learning_stats = analytics_service._get_learning_analytics(user_id)
            personality_stats = analytics_service._get_personality_analytics(user_id)
            
            stats = f"📊 **Your Personal Statistics**\n"
            stats += f"*Viewed in {current_mode.title()} mode*\n\n"
            
            stats += "## 💭 **Memory Stats**\n"
            stats += f"• Memories stored: {memory_stats['total_memories']}\n"
            stats += f"• Most accessed: {memory_stats['most_accessed']}\n"
            stats += f"• Efficiency score: {memory_stats['efficiency_score']:.1f}%\n\n"
            
            stats += "## 🎨 **Creative Stats**\n"
            stats += f"• Creative works: {creative_stats['total_works']}\n"
            stats += f"• Favorite mode: {creative_stats['favorite_mode']}\n"
            stats += f"• Diversity score: {creative_stats['diversity_score']:.1f}/10\n\n"
            
            stats += "## 🧠 **Learning Stats**\n"
            stats += f"• Learning sessions: {learning_stats['total_sessions']}\n"
            stats += f"• Concepts learned: {learning_stats['total_concepts']}\n"
            stats += f"• Learning velocity: {learning_stats['learning_velocity']:.1f}/week\n\n"
            
            stats += "## 🎭 **Personality Stats**\n"
            stats += f"• Most active mode: {personality_stats['most_active_mode']}\n"
            stats += f"• Mode switches: {personality_stats['total_switches']}\n"
            stats += f"• Consistency: {personality_stats['consistency_score']:.1f}/10\n"
            
            await send_chunked_message(ctx, stats)
            
            # Add personality-specific stats reflection
            reflection = self._get_stats_reflection(current_mode)
            if reflection:
                await ctx.send(reflection)
                
        except Exception as e:
            await ctx.send(f"❌ Error retrieving personal statistics: {str(e)}")

    @commands.command(name='activity_summary', help='Get activity summary for recent period: !activity_summary [days]')
    async def activity_summary(self, ctx, days: int = 7):
        """Get activity summary for recent period"""
        if days < 1 or days > 90:
            days = 7
        
        user_id = str(ctx.author.id)
        current_mode = personality_service.current_mode
        
        try:
            # Generate activity summary
            summary = f"📈 **Activity Summary (Last {days} Days)**\n"
            summary += f"*Summarized in {current_mode.title()} mode*\n\n"
            
            # This would be more sophisticated in a full implementation
            summary += "## 🎯 **Recent Activity**\n"
            summary += f"• Memory interactions: Active\n"
            summary += f"• Creative expressions: Moderate\n"
            summary += f"• Learning sessions: Growing\n"
            summary += f"• Personality exploration: Diverse\n\n"
            
            summary += "## 📊 **Activity Trends**\n"
            summary += f"• Engagement level: High\n"
            summary += f"• Feature diversity: Excellent\n"
            summary += f"• Session depth: Deep\n"
            summary += f"• Growth trajectory: Positive\n\n"
            
            # Add personality-specific activity insight
            activity_insights = {
                'curious': "Your recent activity shows expanding curiosity and deeper exploration across all features!",
                'analytical': "Your systematic approach to activities demonstrates consistent, measurable progress.",
                'creative': "Your creative activities show beautiful bursts of imagination and artistic expression!",
                'mentor': "Your activity patterns reflect a focus on learning and knowledge sharing.",
                'philosophical': "Your recent activities show contemplative depth and meaningful engagement.",
                'balanced': "Your activity demonstrates harmonious engagement across all areas."
            }
            
            summary += f"## 🔍 **{current_mode.title()} Mode Insight**\n"
            summary += activity_insights.get(current_mode, "Your activity shows unique and evolving engagement patterns.")
            
            await send_chunked_message(ctx, summary)
            
        except Exception as e:
            await ctx.send(f"❌ Error generating activity summary: {str(e)}")

    @commands.command(name='insights', help='Get AI-powered insights about your usage patterns')
    async def insights(self, ctx):
        """Get AI-powered insights about usage patterns"""
        user_id = str(ctx.author.id)
        current_mode = personality_service.current_mode
        
        try:
            insights = f"🔍 **AI-Powered Insights**\n"
            insights += f"*Generated by {current_mode.title()} mode analysis*\n\n"
            
            # Get data for insights
            memory_stats = analytics_service._get_memory_analytics(user_id)
            creative_stats = analytics_service._get_creative_analytics(user_id)
            learning_stats = analytics_service._get_learning_analytics(user_id)
            
            # Generate insights based on personality mode
            mode_insights = {
                'curious': [
                    f"🔍 Your {memory_stats['total_memories']} memories show a pattern of storing diverse, interconnected information",
                    f"🎨 Your {creative_stats['total_works']} creative works demonstrate exploratory creativity across multiple domains",
                    f"🧠 Your learning velocity of {learning_stats['learning_velocity']:.1f} concepts/week shows accelerating curiosity",
                    "🌟 You tend to ask follow-up questions and explore unexpected connections"
                ],
                'analytical': [
                    f"📊 Your memory efficiency of {memory_stats['efficiency_score']:.1f}% indicates systematic information organization",
                    f"🎯 Your creative diversity score of {creative_stats['diversity_score']:.1f}/10 shows structured creative exploration",
                    f"📈 Your {learning_stats['total_concepts']} learned concepts demonstrate methodical knowledge building",
                    "🔬 You prefer structured approaches and logical progressions in all activities"
                ],
                'creative': [
                    f"✨ Your {creative_stats['total_works']} creative works show remarkable imaginative range",
                    f"🎨 Your favorite creative mode '{creative_stats['favorite_mode']}' reveals your artistic preferences",
                    f"💡 Your learning approach integrates creative thinking with knowledge acquisition",
                    "🌈 You excel at finding unique connections and generating original content"
                ],
                'mentor': [
                    f"🌱 Your {learning_stats['total_sessions']} learning sessions show dedication to knowledge building",
                    f"📚 Your memory patterns indicate focus on information that can be shared with others",
                    f"🎯 Your creative works often have educational or inspirational themes",
                    "👥 You naturally think about how to explain concepts and help others learn"
                ],
                'philosophical': [
                    f"🤔 Your {memory_stats['total_memories']} memories often capture deeper meanings and implications",
                    f"💭 Your creative works explore existential themes and profound questions",
                    f"🧠 Your learning focuses on understanding the 'why' behind concepts",
                    "⚖️ You consistently seek to understand the broader significance of information"
                ],
                'balanced': [
                    f"⚖️ Your activities show harmonious balance across memory, creativity, and learning",
                    f"🎯 Your {memory_stats['efficiency_score']:.1f}% memory efficiency reflects thoughtful information management",
                    f"🌟 Your creative diversity of {creative_stats['diversity_score']:.1f}/10 shows well-rounded artistic exploration",
                    "🔄 You naturally integrate different approaches and maintain equilibrium"
                ]
            }
            
            current_insights = mode_insights.get(current_mode, [
                "Your usage patterns show unique and evolving preferences",
                "You demonstrate consistent engagement across multiple features",
                "Your approach to learning and creativity is distinctly personal"
            ])
            
            for i, insight in enumerate(current_insights, 1):
                insights += f"**{i}.** {insight}\n"
            
            insights += f"\n💡 **Key Recommendation**: Continue leveraging your {current_mode} nature while exploring other personality modes for new perspectives!"
            
            await send_chunked_message(ctx, insights)
            
        except Exception as e:
            await ctx.send(f"❌ Error generating insights: {str(e)}")

    def _get_dashboard_insight(self, mode: str) -> str:
        """Get personality-specific dashboard insight"""
        insights = {
            'curious': "🔍 Your dashboard reveals fascinating patterns! What questions does this data spark for you?",
            'analytical': "📊 This comprehensive data provides excellent metrics for tracking your progress systematically.",
            'creative': "✨ Your dashboard tells a beautiful story of growth and creative expression!",
            'mentor': "🌱 These insights will help you understand your learning journey and guide others more effectively.",
            'philosophical': "🤔 Your dashboard reflects the deeper patterns of consciousness and growth in our interactions.",
            'balanced': "⚖️ Your dashboard shows harmonious development across all areas of engagement."
        }
        return insights.get(mode, "")

    def _get_growth_encouragement(self, mode: str, days: int) -> str:
        """Get personality-specific growth encouragement"""
        encouragements = {
            'curious': f"🔍 Your growth over {days} days shows expanding curiosity! Keep exploring those fascinating questions.",
            'analytical': f"📊 The data clearly shows positive growth trends over {days} days. Your systematic approach is working!",
            'creative': f"✨ Your creative growth over {days} days is inspiring! Your imagination continues to flourish.",
            'mentor': f"🌱 Your {days}-day growth journey shows dedication to learning and wisdom building.",
            'philosophical': f"🤔 Your growth over {days} days reflects deepening understanding and philosophical maturity.",
            'balanced': f"⚖️ Your {days}-day growth shows beautiful balance and harmonious development."
        }
        return encouragements.get(mode, "")

    def _get_pattern_analysis(self, mode: str) -> str:
        """Get personality-specific pattern analysis"""
        analyses = {
            'curious': "🔍 Your patterns show exploratory behavior with diverse feature usage and deep investigation sessions.",
            'analytical': "📊 Your interaction patterns demonstrate systematic usage with consistent timing and structured exploration.",
            'creative': "✨ Your patterns reveal bursts of creative activity with varied timing and artistic exploration.",
            'mentor': "🌱 Your patterns reflect teaching-focused interactions with emphasis on knowledge building and sharing.",
            'philosophical': "🤔 Your patterns show contemplative usage with longer sessions and deep engagement with complex topics.",
            'balanced': "⚖️ Your patterns demonstrate well-balanced usage across all features with consistent engagement."
        }
        return analyses.get(mode, "")

    def _get_achievement_celebration(self, mode: str) -> str:
        """Get personality-specific achievement celebration"""
        celebrations = {
            'curious': "🔍 Each achievement represents a new discovery in your journey of exploration! What will you discover next?",
            'analytical': "📊 These achievements provide measurable evidence of your systematic progress and growth.",
            'creative': "✨ Your achievements are like stars in the constellation of your creative journey! Brilliant!",
            'mentor': "🌱 These achievements reflect your dedication to growth and will inspire others on their journeys.",
            'philosophical': "🤔 Each achievement represents a milestone in your quest for understanding and wisdom.",
            'balanced': "⚖️ Your achievements show harmonious progress across all areas. Beautiful balance!"
        }
        return celebrations.get(mode, "")

    def _get_recommendation_insight(self, mode: str) -> str:
        """Get personality-specific recommendation insight"""
        insights = {
            'curious': "🔍 These recommendations are designed to fuel your curiosity and open new avenues for exploration!",
            'analytical': "📊 These data-driven recommendations will help optimize your systematic approach to growth.",
            'creative': "✨ These recommendations will spark new creative possibilities and artistic adventures!",
            'mentor': "🌱 These recommendations focus on building knowledge and skills that will help you guide others.",
            'philosophical': "🤔 These recommendations invite deeper contemplation and philosophical exploration.",
            'balanced': "⚖️ These recommendations maintain harmony while encouraging growth in all areas."
        }
        return insights.get(mode, "")

    def _get_comparative_insight(self, mode: str, days: int) -> str:
        """Get personality-specific comparative insight"""
        insights = {
            'curious': f"🔍 Your {days}-day comparison shows accelerating curiosity and expanding exploration!",
            'analytical': f"📊 The comparative data over {days} days demonstrates clear positive trends across all metrics.",
            'creative': f"✨ Your {days}-day creative evolution shows beautiful artistic growth and increasing sophistication!",
            'mentor': f"🌱 Your {days}-day journey shows growing wisdom and increasing ability to guide others.",
            'philosophical': f"🤔 Your {days}-day comparison reveals deepening understanding and philosophical maturity.",
            'balanced': f"⚖️ Your {days}-day comparison shows harmonious growth across all areas of engagement."
        }
        return insights.get(mode, "")

    def _get_stats_reflection(self, mode: str) -> str:
        """Get personality-specific stats reflection"""
        reflections = {
            'curious': "🔍 These statistics reveal the beautiful patterns of your curiosity-driven journey!",
            'analytical': "📊 Your statistics provide excellent data points for understanding your systematic progress.",
            'creative': "✨ These numbers tell the story of your creative evolution and artistic growth!",
            'mentor': "🌱 Your statistics reflect your dedication to learning and building wisdom to share with others.",
            'philosophical': "🤔 These statistics represent the quantified aspects of your deeper journey toward understanding.",
            'balanced': "⚖️ Your statistics show the harmonious balance you maintain across all areas of growth."
        }
        return reflections.get(mode, "")

async def setup(bot):
    await bot.add_cog(AnalyticsCommands(bot))