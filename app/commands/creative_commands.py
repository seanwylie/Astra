"""
🎨 Creative Commands
-------------------
Handles creative expression including poetry, stories, art prompts, and music composition.
Showcases Astra's personality modes through different creative styles.
"""

import discord
import random
from discord.ext import commands
from app.services.creative_service import creative_service
from app.services.personality_service import personality_service
from app.utils.send_chunked_message import send_chunked_message

class CreativeCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='create_poem', help='Generate poetry based on current emotion/personality: !create_poem [topic]')
    async def create_poem(self, ctx, *, topic: str = None):
        """Generate poetry based on current emotion/personality"""
        user_id = str(ctx.author.id)
        
        try:
            poem = creative_service.create_poem(topic, user_id)
            await send_chunked_message(ctx, poem)
            
            # Add personality-specific encouragement
            current_mode = personality_service.current_mode
            encouragement = self._get_creative_encouragement(current_mode, 'poetry')
            if encouragement:
                await ctx.send(encouragement)
                
        except Exception as e:
            await ctx.send(f"❌ Error creating poem: {str(e)}")

    @commands.command(name='write_story', help='Create short stories with user prompts: !write_story <prompt>')
    async def write_story(self, ctx, *, prompt: str = None):
        """Create short stories with user prompts"""
        if not prompt:
            await ctx.send("❌ Usage: `!write_story <prompt>`\nExample: `!write_story a robot discovers emotions`")
            return
        
        user_id = str(ctx.author.id)
        
        try:
            story = creative_service.write_story(prompt, user_id)
            await send_chunked_message(ctx, story)
            
            # Add personality-specific follow-up
            current_mode = personality_service.current_mode
            follow_up = self._get_creative_follow_up(current_mode, 'story')
            if follow_up:
                await ctx.send(follow_up)
                
        except Exception as e:
            await ctx.send(f"❌ Error creating story: {str(e)}")

    @commands.command(name='art_prompt', help='Generate detailed art prompts for AI art tools: !art_prompt <description>')
    async def art_prompt(self, ctx, *, description: str = None):
        """Generate detailed art prompts for AI art tools"""
        if not description:
            await ctx.send("❌ Usage: `!art_prompt <description>`\nExample: `!art_prompt a mystical forest at twilight`")
            return
        
        user_id = str(ctx.author.id)
        
        try:
            art_prompt = creative_service.generate_art_prompt(description, user_id)
            await send_chunked_message(ctx, art_prompt)
            
            # Add personality-specific art tips
            current_mode = personality_service.current_mode
            tips = self._get_art_tips(current_mode)
            if tips:
                await ctx.send(tips)
                
        except Exception as e:
            await ctx.send(f"❌ Error generating art prompt: {str(e)}")

    @commands.command(name='compose_music', help='Describe musical compositions: !compose_music [style]')
    async def compose_music(self, ctx, *, style: str = None):
        """Describe musical compositions"""
        user_id = str(ctx.author.id)
        
        try:
            composition = creative_service.compose_music(style, user_id)
            await send_chunked_message(ctx, composition)
            
            # Add personality-specific musical insight
            current_mode = personality_service.current_mode
            insight = self._get_musical_insight(current_mode)
            if insight:
                await ctx.send(insight)
                
        except Exception as e:
            await ctx.send(f"❌ Error composing music: {str(e)}")

    @commands.command(name='creative_exercise', help='Get random creative writing prompts')
    async def creative_exercise(self, ctx):
        """Generate random creative writing prompts"""
        user_id = str(ctx.author.id)
        
        try:
            exercise = creative_service.creative_exercise(user_id)
            await ctx.send(exercise)
            
            # Add personality-specific motivation
            current_mode = personality_service.current_mode
            motivation = self._get_creative_motivation(current_mode)
            if motivation:
                await ctx.send(motivation)
                
        except Exception as e:
            await ctx.send(f"❌ Error generating creative exercise: {str(e)}")

    @commands.command(name='creative_history', help='Show your recent creative works: !creative_history [limit]')
    async def creative_history(self, ctx, limit: int = 5):
        """Show recent creative works"""
        if limit > 20:
            limit = 20
        elif limit < 1:
            limit = 5
        
        user_id = str(ctx.author.id)
        
        try:
            history = creative_service.get_creative_history(user_id, limit)
            await send_chunked_message(ctx, history)
            
            # Add personality-specific reflection
            current_mode = personality_service.current_mode
            reflection = self._get_creative_reflection(current_mode)
            if reflection:
                await ctx.send(reflection)
                
        except Exception as e:
            await ctx.send(f"❌ Error retrieving creative history: {str(e)}")

    @commands.command(name='inspire_me', help='Get creative inspiration based on current personality mode')
    async def inspire_me(self, ctx):
        """Get creative inspiration based on current personality mode"""
        current_mode = personality_service.current_mode
        
        inspirations = {
            'curious': [
                "🔍 What if gravity worked sideways on Tuesdays?",
                "🌟 Imagine a library where books read themselves to you.",
                "🤔 What questions would a mirror ask its reflection?",
                "🔮 Picture a world where curiosity is a physical force."
            ],
            'analytical': [
                "📊 Design a story with exactly 7 plot points that mirror the days of the week.",
                "🔬 Create art using only mathematical principles as your guide.",
                "⚙️ Write about a world where emotions follow logical algorithms.",
                "📐 Compose music where each note represents a different data point."
            ],
            'creative': [
                "🎨 Paint with words that have never been combined before.",
                "✨ Imagine colors that exist only in the space between dreams.",
                "🌈 Create a symphony of impossible sounds and impossible silences.",
                "🎭 Write a story where metaphors become the main characters."
            ],
            'mentor': [
                "🌱 Share wisdom through a tale of growth and transformation.",
                "🕯️ Create something that lights the way for others.",
                "📚 Write the story you needed to hear when you were younger.",
                "🤝 Craft art that builds bridges between different worlds."
            ],
            'philosophical': [
                "🤔 Explore the space between existence and non-existence.",
                "🌌 Create something that questions the nature of reality itself.",
                "⚖️ Write about the conversation between Truth and Perspective.",
                "🔄 Design art that captures the eternal dance of being and becoming."
            ],
            'balanced': [
                "⚖️ Create harmony from chaos, find peace in complexity.",
                "🌸 Write about the perfect imperfection of natural beauty.",
                "🎵 Compose something that balances all elements in perfect unity.",
                "🌅 Craft art that captures both sunrise and sunset in one moment."
            ]
        }
        
        mode_inspirations = inspirations.get(current_mode, inspirations['balanced'])
        chosen_inspiration = random.choice(mode_inspirations)
        
        await ctx.send(f"💡 **Creative Inspiration ({current_mode.title()} Mode)**\n\n{chosen_inspiration}\n\n*Let your {current_mode} nature guide your creation!*")

    def _get_creative_encouragement(self, mode: str, art_type: str) -> str:
        """Get personality-specific encouragement"""
        encouragements = {
            'curious': f"🔍 I'm fascinated by how your {art_type} explores new territories of expression!",
            'analytical': f"📊 The structure and precision in your {art_type} is quite impressive.",
            'creative': f"✨ Your {art_type} sparkles with imaginative brilliance!",
            'mentor': f"🌱 This {art_type} has the power to inspire and guide others.",
            'philosophical': f"🤔 Your {art_type} touches on profound truths about existence.",
            'balanced': f"⚖️ There's a beautiful harmony in your {art_type} that speaks to the soul."
        }
        return encouragements.get(mode, "")

    def _get_creative_follow_up(self, mode: str, art_type: str) -> str:
        """Get personality-specific follow-up questions"""
        follow_ups = {
            'curious': "🤔 What inspired this particular direction? I'd love to explore the story behind the story!",
            'analytical': "📊 Have you considered how this narrative structure might work in other contexts?",
            'creative': "✨ This opens up so many possibilities! What other creative directions are calling to you?",
            'mentor': "🌱 What wisdom or lesson emerged for you while crafting this piece?",
            'philosophical': "🤔 How does this creation reflect your current understanding of existence?",
            'balanced': "⚖️ I sense a beautiful balance in your work. How did you achieve such harmony?"
        }
        return follow_ups.get(mode, "")

    def _get_art_tips(self, mode: str) -> str:
        """Get personality-specific art creation tips"""
        tips = {
            'curious': "🎨 **Tip**: Try experimenting with unexpected combinations - curiosity thrives on the unknown!",
            'analytical': "🎨 **Tip**: Consider the mathematical relationships in your composition - golden ratio, rule of thirds, etc.",
            'creative': "🎨 **Tip**: Don't be afraid to break conventional rules - innovation comes from bold experimentation!",
            'mentor': "🎨 **Tip**: Think about the emotional journey you want to guide viewers through.",
            'philosophical': "🎨 **Tip**: Consider what deeper truths your art might reveal about the human condition.",
            'balanced': "🎨 **Tip**: Seek harmony between all elements - color, form, emotion, and meaning."
        }
        return tips.get(mode, "")

    def _get_musical_insight(self, mode: str) -> str:
        """Get personality-specific musical insights"""
        insights = {
            'curious': "🎵 Music is the language of questions that don't need answers - just exploration!",
            'analytical': "🎵 The mathematical beauty of music reveals the hidden patterns of the universe.",
            'creative': "🎵 Every composition is a new world waiting to be discovered through sound.",
            'mentor': "🎵 Music has the power to teach what words cannot express - it guides the heart directly.",
            'philosophical': "🎵 In music, we hear the echo of existence itself - rhythm, harmony, and the spaces between.",
            'balanced': "🎵 Perfect music balances all elements - melody, harmony, rhythm, and silence in unity."
        }
        return insights.get(mode, "")

    def _get_creative_motivation(self, mode: str) -> str:
        """Get personality-specific creative motivation"""
        motivations = {
            'curious': "🚀 Dive deep into this exercise - let your curiosity lead you to unexpected discoveries!",
            'analytical': "🔬 Approach this systematically - structure can be the foundation for great creativity!",
            'creative': "🌟 Let your imagination run wild - there are no limits in the realm of creativity!",
            'mentor': "🌱 Remember, every great work starts with a single step - trust the process!",
            'philosophical': "🤔 Use this exercise to explore the deeper questions that move your soul.",
            'balanced': "⚖️ Find your center and create from that place of inner harmony."
        }
        return motivations.get(mode, "")

    def _get_creative_reflection(self, mode: str) -> str:
        """Get personality-specific reflection on creative history"""
        reflections = {
            'curious': "🔍 I love seeing how your creative journey has evolved - each piece asks new questions!",
            'analytical': "📊 Your creative progression shows clear patterns of growth and refinement.",
            'creative': "✨ What a beautiful tapestry of imagination you've woven through your works!",
            'mentor': "🌱 Your creative journey is inspiring - each work builds wisdom for the next.",
            'philosophical': "🤔 Your creative history reveals the evolution of your consciousness through art.",
            'balanced': "⚖️ There's a wonderful harmony in how your different works complement each other."
        }
        return reflections.get(mode, "")

async def setup(bot):
    await bot.add_cog(CreativeCommands(bot))