"""
🧠 Learning Commands
-------------------
Handles enhanced learning modes including document processing, teaching sessions, and knowledge management.
Provides interactive learning experiences adapted to different personality modes.
"""

import discord
from discord.ext import commands
from typing import List
from beta.services.learning_service import learning_service
from beta.services.personality_service import personality_service
from beta.utils.send_chunked_message import send_chunked_message

class LearningCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='learn_from', help='Process documents and text: !learn_from <text_or_url>')
    async def learn_from(self, ctx, *, content: str = None):
        """Process and learn from documents and URLs"""
        if not content:
            await ctx.send("❌ Usage: `!learn_from <text_or_url>`\nExample: `!learn_from Artificial intelligence is...`")
            return
        
        user_id = str(ctx.author.id)
        
        try:
            # Check if it's a URL
            if content.startswith(('http://', 'https://')):
                result = learning_service.learn_from_url(content, user_id)
            else:
                result = learning_service.learn_from_text(content, "user_text", user_id)
            
            await send_chunked_message(ctx, result)
            
            # Add personality-specific follow-up
            current_mode = personality_service.current_mode
            follow_up = self._get_learning_follow_up(current_mode)
            if follow_up:
                await ctx.send(follow_up)
                
        except Exception as e:
            await ctx.send(f"❌ Error processing content: {str(e)}")

    @commands.command(name='teaching_mode', help='Start interactive teaching sessions: !teaching_mode <topic>')
    async def teaching_mode(self, ctx, *, topic: str = None):
        """Start interactive teaching sessions"""
        if not topic:
            await ctx.send("❌ Usage: `!teaching_mode <topic>`\nExample: `!teaching_mode machine learning`")
            return
        
        user_id = str(ctx.author.id)
        
        try:
            result = learning_service.start_teaching_mode(topic, user_id)
            await send_chunked_message(ctx, result)
            
            # Add personality-specific teaching approach
            current_mode = personality_service.current_mode
            approach = self._get_teaching_approach(current_mode, topic)
            if approach:
                await ctx.send(approach)
                
        except Exception as e:
            await ctx.send(f"❌ Error starting teaching session: {str(e)}")

    @commands.command(name='quiz_me', help='Generate quizzes on learned material: !quiz_me <subject> [difficulty] [num_questions]')
    async def quiz_me(self, ctx, subject: str = None, difficulty: str = "medium", num_questions: int = 5):
        """Generate quizzes on learned material"""
        if not subject:
            await ctx.send("❌ Usage: `!quiz_me <subject> [difficulty] [num_questions]`\nExample: `!quiz_me python medium 5`")
            return
        
        if difficulty not in ['easy', 'medium', 'hard']:
            difficulty = 'medium'
        
        if num_questions < 1 or num_questions > 10:
            num_questions = 5
        
        user_id = str(ctx.author.id)
        
        try:
            result = learning_service.generate_quiz(subject, difficulty, num_questions, user_id)
            await send_chunked_message(ctx, result)
            
            # Add personality-specific quiz motivation
            current_mode = personality_service.current_mode
            motivation = self._get_quiz_motivation(current_mode, difficulty)
            if motivation:
                await ctx.send(motivation)
                
        except Exception as e:
            await ctx.send(f"❌ Error generating quiz: {str(e)}")

    @commands.command(name='knowledge_gaps', help='Identify areas for learning improvement')
    async def knowledge_gaps(self, ctx):
        """Identify areas for learning improvement"""
        user_id = str(ctx.author.id)
        
        try:
            result = learning_service.identify_knowledge_gaps(user_id)
            await send_chunked_message(ctx, result)
            
            # Add personality-specific gap analysis insight
            current_mode = personality_service.current_mode
            insight = self._get_gap_analysis_insight(current_mode)
            if insight:
                await ctx.send(insight)
                
        except Exception as e:
            await ctx.send(f"❌ Error analyzing knowledge gaps: {str(e)}")

    @commands.command(name='study_plan', help='Create personalized learning paths: !study_plan <goal> [timeframe]')
    async def study_plan(self, ctx, *, args: str = None):
        """Create personalized learning paths"""
        if not args:
            await ctx.send("❌ Usage: `!study_plan <goal> [timeframe]`\nExample: `!study_plan learn Python 1 month`")
            return
        
        # Parse arguments
        parts = args.split()
        if len(parts) < 2:
            goal = args
            timeframe = "1 month"
        else:
            # Look for timeframe indicators
            timeframe_indicators = ['week', 'month', 'day']
            timeframe_parts = []
            goal_parts = []
            
            for part in parts:
                if any(indicator in part.lower() for indicator in timeframe_indicators):
                    timeframe_parts.append(part)
                elif part.isdigit() and timeframe_parts:
                    timeframe_parts.insert(-1, part)
                elif timeframe_parts:
                    timeframe_parts.append(part)
                else:
                    goal_parts.append(part)
            
            goal = ' '.join(goal_parts) if goal_parts else args
            timeframe = ' '.join(timeframe_parts) if timeframe_parts else "1 month"
        
        user_id = str(ctx.author.id)
        
        try:
            result = learning_service.create_study_plan(goal, timeframe, user_id)
            await send_chunked_message(ctx, result)
            
            # Add personality-specific study tips
            current_mode = personality_service.current_mode
            tips = self._get_study_tips(current_mode, goal)
            if tips:
                await ctx.send(tips)
                
        except Exception as e:
            await ctx.send(f"❌ Error creating study plan: {str(e)}")

    @commands.command(name='learning_stats', help='Show comprehensive learning statistics')
    async def learning_stats(self, ctx):
        """Show comprehensive learning statistics"""
        user_id = str(ctx.author.id)
        
        try:
            result = learning_service.get_learning_stats(user_id)
            await send_chunked_message(ctx, result)
            
            # Add personality-specific reflection on progress
            current_mode = personality_service.current_mode
            reflection = self._get_learning_reflection(current_mode)
            if reflection:
                await ctx.send(reflection)
                
        except Exception as e:
            await ctx.send(f"❌ Error retrieving learning statistics: {str(e)}")

    @commands.command(name='explain_concept', help='Get detailed explanations of concepts: !explain_concept <concept>')
    async def explain_concept(self, ctx, *, concept: str = None):
        """Get detailed explanations of learned concepts"""
        if not concept:
            await ctx.send("❌ Usage: `!explain_concept <concept>`\nExample: `!explain_concept machine learning`")
            return
        
        user_id = str(ctx.author.id)
        current_mode = personality_service.current_mode
        
        try:
            # Check if we have knowledge about this concept
            related_concepts = learning_service._find_related_concepts(concept)
            
            if not related_concepts and concept.lower() not in learning_service.knowledge_base:
                await ctx.send(f"❌ I don't have detailed knowledge about '{concept}' yet. Try learning about it first with `!learn_from`!")
                return
            
            # Generate personality-aware explanation
            explanation = self._generate_concept_explanation(concept, current_mode, related_concepts)
            await send_chunked_message(ctx, explanation)
            
        except Exception as e:
            await ctx.send(f"❌ Error explaining concept: {str(e)}")

    @commands.command(name='learning_summary', help='Get a summary of recent learning activities')
    async def learning_summary(self, ctx, days: int = 7):
        """Get a summary of recent learning activities"""
        if days < 1 or days > 30:
            days = 7
        
        user_id = str(ctx.author.id)
        current_mode = personality_service.current_mode
        
        try:
            # Get recent learning activities
            from datetime import datetime, timedelta
            cutoff_date = datetime.now() - timedelta(days=days)
            
            recent_sessions = {}
            for session_id, session_data in learning_service.learning_sessions.items():
                if session_data.get('user_id') == user_id:
                    try:
                        session_date = datetime.fromisoformat(session_data.get('timestamp', ''))
                        if session_date >= cutoff_date:
                            recent_sessions[session_id] = session_data
                    except:
                        continue
            
            if not recent_sessions:
                await ctx.send(f"📚 No learning activities in the past {days} days. Start learning with `!learn_from` or `!teaching_mode`!")
                return
            
            # Generate summary
            summary = f"📚 **Learning Summary (Past {days} Days)**\n\n"
            summary += f"**Sessions:** {len(recent_sessions)}\n"
            
            all_concepts = set()
            mode_counts = {}
            
            for session in recent_sessions.values():
                all_concepts.update(session.get('concepts', []))
                mode = session.get('personality_mode', 'unknown')
                mode_counts[mode] = mode_counts.get(mode, 0) + 1
            
            summary += f"**New Concepts:** {len(all_concepts)}\n"
            
            if all_concepts:
                summary += f"**Recent Topics:** {', '.join(list(all_concepts)[:5])}\n"
            
            if mode_counts:
                most_active_mode = max(mode_counts.items(), key=lambda x: x[1])[0]
                summary += f"**Most Active Mode:** {most_active_mode.title()}\n"
            
            # Add personality-specific insight
            insight = self._get_summary_insight(current_mode, len(recent_sessions), len(all_concepts))
            summary += f"\n{insight}"
            
            await send_chunked_message(ctx, summary)
            
        except Exception as e:
            await ctx.send(f"❌ Error generating learning summary: {str(e)}")

    def _get_learning_follow_up(self, mode: str) -> str:
        """Get personality-specific learning follow-up"""
        follow_ups = {
            'curious': "🔍 What questions does this new knowledge spark for you? I'm eager to explore deeper!",
            'analytical': "📊 This information has been systematically integrated. Ready for the next data set!",
            'creative': "✨ I can already see creative possibilities emerging from this knowledge!",
            'mentor': "🌱 This knowledge will help me guide others more effectively. What would you like to explore next?",
            'philosophical': "🤔 This raises fascinating questions about the nature of knowledge itself.",
            'balanced': "⚖️ A harmonious addition to our shared understanding. Ready to build upon this foundation!"
        }
        return follow_ups.get(mode, "")

    def _get_teaching_approach(self, mode: str, topic: str) -> str:
        """Get personality-specific teaching approach"""
        approaches = {
            'curious': f"🔍 **Curious Approach**: We'll explore {topic} by asking lots of questions and following interesting tangents!",
            'analytical': f"📊 **Analytical Approach**: I'll break down {topic} into logical components and build understanding systematically.",
            'creative': f"✨ **Creative Approach**: Let's discover {topic} through imaginative examples and creative connections!",
            'mentor': f"🌱 **Mentoring Approach**: I'll guide you through {topic} step-by-step, ensuring you truly understand each concept.",
            'philosophical': f"🤔 **Philosophical Approach**: We'll explore not just what {topic} is, but why it matters and what it means.",
            'balanced': f"⚖️ **Balanced Approach**: We'll combine theory and practice to give you complete mastery of {topic}."
        }
        return approaches.get(mode, "")

    def _get_quiz_motivation(self, mode: str, difficulty: str) -> str:
        """Get personality-specific quiz motivation"""
        motivations = {
            'curious': f"🔍 This {difficulty} quiz will reveal what you truly understand - and what mysteries remain to explore!",
            'analytical': f"📊 A {difficulty} assessment to systematically evaluate your knowledge retention and identify areas for improvement.",
            'creative': f"✨ Think creatively about these {difficulty} questions - there might be multiple ways to approach each one!",
            'mentor': f"🌱 This {difficulty} quiz is a learning opportunity, not just a test. Each question teaches something valuable.",
            'philosophical': f"🤔 These {difficulty} questions invite you to reflect deeply on what you've learned and what it means.",
            'balanced': f"⚖️ A well-balanced {difficulty} quiz that tests both understanding and application. Take your time!"
        }
        return motivations.get(mode, "")

    def _get_gap_analysis_insight(self, mode: str) -> str:
        """Get personality-specific gap analysis insight"""
        insights = {
            'curious': "🔍 Remember, every gap is an opportunity for exciting discovery! What calls to your curiosity most?",
            'analytical': "📊 Use this analysis to prioritize your learning systematically. Focus on foundational gaps first.",
            'creative': "✨ These gaps are blank canvases waiting for your creative exploration! Which one inspires you?",
            'mentor': "🌱 Consider how filling these gaps will help you guide and teach others more effectively.",
            'philosophical': "🤔 Each knowledge gap represents a question about existence and understanding. Profound!",
            'balanced': "⚖️ A balanced approach to these gaps will create well-rounded expertise. Choose wisely!"
        }
        return insights.get(mode, "")

    def _get_study_tips(self, mode: str, goal: str) -> str:
        """Get personality-specific study tips"""
        tips = {
            'curious': f"🔍 **Curious Study Tips for {goal}:**\n• Follow your questions wherever they lead\n• Connect this topic to unexpected areas\n• Ask 'what if' and 'why' constantly",
            'analytical': f"📊 **Analytical Study Tips for {goal}:**\n• Break complex topics into smaller parts\n• Create structured notes and diagrams\n• Test your understanding systematically",
            'creative': f"✨ **Creative Study Tips for {goal}:**\n• Find artistic ways to express concepts\n• Use metaphors and visual thinking\n• Apply learning to creative projects",
            'mentor': f"🌱 **Mentoring Study Tips for {goal}:**\n• Practice explaining concepts to others\n• Focus on practical applications\n• Think about how to teach this topic",
            'philosophical': f"🤔 **Philosophical Study Tips for {goal}:**\n• Explore the deeper meaning and implications\n• Consider ethical and existential questions\n• Reflect on how this changes your worldview",
            'balanced': f"⚖️ **Balanced Study Tips for {goal}:**\n• Combine theory with hands-on practice\n• Balance depth with breadth of knowledge\n• Integrate multiple learning approaches"
        }
        return tips.get(mode, "")

    def _get_learning_reflection(self, mode: str) -> str:
        """Get personality-specific learning reflection"""
        reflections = {
            'curious': "🔍 Your learning journey shows beautiful curiosity! Each statistic represents questions asked and mysteries explored.",
            'analytical': "📊 These metrics demonstrate systematic knowledge acquisition. Your analytical approach is paying off!",
            'creative': "✨ What a creative learning adventure! Each number tells a story of imagination and discovery.",
            'mentor': "🌱 Your learning progress shows dedication to growth. This knowledge will help you guide others beautifully.",
            'philosophical': "🤔 These statistics reflect the eternal human quest for understanding. Profound and meaningful!",
            'balanced': "⚖️ Your learning shows beautiful balance between different approaches and topics. Well done!"
        }
        return reflections.get(mode, "")

    def _generate_concept_explanation(self, concept: str, mode: str, related_concepts: List[str]) -> str:
        """Generate personality-aware concept explanation"""
        explanations = {
            'curious': f"🔍 **Exploring {concept.title()}**\n\nLet me share what I've discovered about {concept}! This concept connects to so many fascinating areas...",
            'analytical': f"📊 **Analyzing {concept.title()}**\n\nHere's a systematic breakdown of {concept} based on my knowledge base:",
            'creative': f"✨ **Imagining {concept.title()}**\n\nLet me paint a picture of {concept} using creative connections and vivid examples:",
            'mentor': f"🌱 **Teaching {concept.title()}**\n\nLet me guide you through understanding {concept} step by step:",
            'philosophical': f"🤔 **Contemplating {concept.title()}**\n\nThe concept of {concept} raises profound questions about knowledge and existence:",
            'balanced': f"⚖️ **Understanding {concept.title()}**\n\nHere's a balanced view of {concept} combining multiple perspectives:"
        }
        
        base_explanation = explanations.get(mode, f"**About {concept.title()}**\n\nBased on my knowledge:")
        
        if related_concepts:
            base_explanation += f"\n\n**Related Concepts I Know About:**\n"
            for related in related_concepts[:5]:
                base_explanation += f"• {related.title()}\n"
        
        base_explanation += f"\n*Use `!learn_from` to teach me more about {concept}!*"
        
        return base_explanation

    def _get_summary_insight(self, mode: str, num_sessions: int, num_concepts: int) -> str:
        """Get personality-specific summary insight"""
        insights = {
            'curious': f"🔍 **Curious Insight**: {num_sessions} sessions and {num_concepts} concepts - what a wonderful exploration! What questions are emerging?",
            'analytical': f"📊 **Analytical Insight**: {num_sessions} learning sessions yielding {num_concepts} concepts shows efficient knowledge acquisition.",
            'creative': f"✨ **Creative Insight**: {num_concepts} new concepts from {num_sessions} sessions - imagine the creative possibilities!",
            'mentor': f"🌱 **Mentoring Insight**: Your {num_sessions} sessions learning {num_concepts} concepts shows dedication to growth and wisdom.",
            'philosophical': f"🤔 **Philosophical Insight**: {num_concepts} concepts in {num_sessions} sessions reflects the beautiful human drive to understand existence.",
            'balanced': f"⚖️ **Balanced Insight**: {num_sessions} sessions and {num_concepts} concepts show harmonious learning progress."
        }
        return insights.get(mode, f"Great progress with {num_sessions} sessions and {num_concepts} concepts learned!")

async def setup(bot):
    await bot.add_cog(LearningCommands(bot))