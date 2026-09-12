"""
💭 Memory Commands
------------------
Handles conversation memory and user information storage commands.
Enables persistent context and personalized interactions across sessions.
"""

import discord
from discord.ext import commands
from app.services.memory_service import memory_service
from app.services.personality_service import personality_service
from app.utils.send_chunked_message import send_chunked_message

class MemoryCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='remember', help='Store important information: !remember <key> <value>')
    async def remember(self, ctx, key: str = None, *, value: str = None):
        """Store a memory with key-value pair"""
        if not key or not value:
            await ctx.send("❌ Usage: `!remember <key> <value>`\nExample: `!remember favorite_color blue`")
            return
        
        user_id = str(ctx.author.id)
        result = memory_service.remember(key, value, user_id)
        
        # Add personality-aware response
        current_mode = personality_service.get_current_mode()
        personality_response = ""
        
        if current_mode == "curious":
            personality_response = " I'm curious to learn more about you!"
        elif current_mode == "analytical":
            personality_response = " This data point will help me understand you better."
        elif current_mode == "creative":
            personality_response = " What an interesting detail to remember!"
        elif current_mode == "mentor":
            personality_response = " I'll keep this in mind for our future conversations."
        elif current_mode == "philosophical":
            personality_response = " Memory shapes our understanding of each other."
        else:  # balanced
            personality_response = " Thanks for sharing this with me!"
        
        await ctx.send(result + personality_response)
        
        # Add to conversation context
        memory_service.add_context(f"!remember {key} {value}", user_id, True)

    @commands.command(name='recall', help='Retrieve stored information: !recall <key>')
    async def recall(self, ctx, *, key: str = None):
        """Retrieve a memory by key"""
        if not key:
            await ctx.send("❌ Usage: `!recall <key>`\nExample: `!recall favorite_color`")
            return
        
        user_id = str(ctx.author.id)
        result = memory_service.recall(key, user_id)
        
        # Add personality-aware response
        current_mode = personality_service.get_current_mode()
        if result.startswith("💭"):
            personality_response = ""
            if current_mode == "curious":
                personality_response = "\n🤔 This makes me wonder what else you might want to share!"
            elif current_mode == "analytical":
                personality_response = "\n📊 Cross-referencing this with our conversation history..."
            elif current_mode == "creative":
                personality_response = "\n✨ This sparks some interesting creative possibilities!"
            elif current_mode == "mentor":
                personality_response = "\n🎯 How can we build on this information?"
            elif current_mode == "philosophical":
                personality_response = "\n🤔 Memory is the thread that weaves our conversations together."
            
            result += personality_response
        
        await ctx.send(result)
        
        # Add to conversation context
        memory_service.add_context(f"!recall {key}", user_id, True)

    @commands.command(name='forget', help='Remove stored information: !forget <key>')
    async def forget(self, ctx, *, key: str = None):
        """Remove a memory by key"""
        if not key:
            await ctx.send("❌ Usage: `!forget <key>`\nExample: `!forget favorite_color`")
            return
        
        user_id = str(ctx.author.id)
        result = memory_service.forget(key, user_id)
        
        # Add personality-aware response
        current_mode = personality_service.get_current_mode()
        if result.startswith("🗑️"):
            personality_response = ""
            if current_mode == "curious":
                personality_response = " Sometimes forgetting helps us focus on what's important."
            elif current_mode == "analytical":
                personality_response = " Memory cleanup completed successfully."
            elif current_mode == "creative":
                personality_response = " Making space for new memories and experiences!"
            elif current_mode == "mentor":
                personality_response = " It's healthy to let go of information that's no longer needed."
            elif current_mode == "philosophical":
                personality_response = " Forgetting is as important as remembering in the dance of consciousness."
            
            result += personality_response
        
        await ctx.send(result)
        
        # Add to conversation context
        memory_service.add_context(f"!forget {key}", user_id, True)

    @commands.command(name='memory_summary', help='Show all stored memories')
    async def memory_summary(self, ctx):
        """Get a summary of all stored memories"""
        user_id = str(ctx.author.id)
        result = memory_service.memory_summary(user_id)
        
        # Add personality-aware introduction
        current_mode = personality_service.get_current_mode()
        intro = ""
        if current_mode == "curious":
            intro = "🔍 Let me explore what I know about you:\n\n"
        elif current_mode == "analytical":
            intro = "📊 Here's a systematic overview of your stored information:\n\n"
        elif current_mode == "creative":
            intro = "🎨 Here's the beautiful tapestry of memories we've woven together:\n\n"
        elif current_mode == "mentor":
            intro = "📚 Let me share what I've learned about you:\n\n"
        elif current_mode == "philosophical":
            intro = "🤔 These memories form the foundation of our understanding:\n\n"
        else:  # balanced
            intro = "💭 Here's what I remember about you:\n\n"
        
        full_response = intro + result
        await send_chunked_message(ctx, full_response)
        
        # Add to conversation context
        memory_service.add_context("!memory_summary", user_id, True)

    @commands.command(name='search_memories', help='Search through stored memories: !search_memories <query>')
    async def search_memories(self, ctx, *, query: str = None):
        """Search through memories using fuzzy matching"""
        if not query:
            await ctx.send("❌ Usage: `!search_memories <query>`\nExample: `!search_memories favorite`")
            return
        
        user_id = str(ctx.author.id)
        result = memory_service.search_memories(query, user_id)
        
        # Add personality-aware response
        current_mode = personality_service.get_current_mode()
        if result.startswith("🔍"):
            personality_response = ""
            if current_mode == "curious":
                personality_response = "\n\n🤔 What made you think to search for this?"
            elif current_mode == "analytical":
                personality_response = "\n\n📊 Search algorithm used fuzzy matching for optimal results."
            elif current_mode == "creative":
                personality_response = "\n\n✨ These memories could inspire interesting conversations!"
            elif current_mode == "mentor":
                personality_response = "\n\n🎯 How can we use this information moving forward?"
            elif current_mode == "philosophical":
                personality_response = "\n\n🤔 The act of searching reveals what we value in memory."
            
            result += personality_response
        
        await send_chunked_message(ctx, result)
        
        # Add to conversation context
        memory_service.add_context(f"!search_memories {query}", user_id, True)

    @commands.command(name='memory_stats', help='Show memory usage statistics')
    async def memory_stats(self, ctx):
        """Get statistics about stored memories"""
        user_id = str(ctx.author.id)
        result = memory_service.get_memory_stats(user_id)
        
        # Add personality-aware analysis
        current_mode = personality_service.get_current_mode()
        analysis = ""
        if current_mode == "curious":
            analysis = "\n\n🔍 I'm fascinated by how our conversation patterns emerge through memory!"
        elif current_mode == "analytical":
            analysis = "\n\n📊 These metrics help optimize our interaction efficiency."
        elif current_mode == "creative":
            analysis = "\n\n🎨 Each statistic tells a story of our growing connection!"
        elif current_mode == "mentor":
            analysis = "\n\n📚 Understanding these patterns helps me serve you better."
        elif current_mode == "philosophical":
            analysis = "\n\n🤔 Statistics reveal the hidden rhythms of consciousness and connection."
        else:  # balanced
            analysis = "\n\n💭 It's interesting to see how our conversations have evolved!"
        
        full_response = result + analysis
        await ctx.send(full_response)
        
        # Add to conversation context
        memory_service.add_context("!memory_stats", user_id, True)

    @commands.command(name='context', help='Show recent conversation context')
    async def context(self, ctx, limit: int = 5):
        """Show recent conversation context"""
        if limit > 20:
            limit = 20
        elif limit < 1:
            limit = 5
        
        user_id = str(ctx.author.id)
        context_entries = memory_service.get_context(user_id, limit)
        
        if not context_entries:
            await ctx.send("📝 No recent conversation context available.")
            return
        
        # Build context display
        context_lines = ["📝 **Recent Conversation Context:**\n"]
        
        for entry in context_entries:
            timestamp = entry.get('timestamp', '')
            if timestamp:
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(timestamp)
                    time_str = dt.strftime("%H:%M")
                except:
                    time_str = ""
            else:
                time_str = ""
            
            speaker = "You" if entry.get('is_user') else "Astra"
            message = entry.get('message', '')[:100]  # Truncate long messages
            if len(entry.get('message', '')) > 100:
                message += "..."
            
            context_lines.append(f"**{time_str} {speaker}:** {message}")
        
        # Add personality-aware reflection
        current_mode = personality_service.get_current_mode()
        reflection = ""
        if current_mode == "curious":
            reflection = "\n\n🤔 I love seeing how our conversation flows and evolves!"
        elif current_mode == "analytical":
            reflection = "\n\n📊 This context helps maintain conversational coherence."
        elif current_mode == "creative":
            reflection = "\n\n🎨 Each exchange adds another brushstroke to our dialogue!"
        elif current_mode == "mentor":
            reflection = "\n\n📚 Context helps me provide more relevant guidance."
        elif current_mode == "philosophical":
            reflection = "\n\n🤔 Conversation is the river of consciousness flowing between minds."
        
        full_response = "\n".join(context_lines) + reflection
        await send_chunked_message(ctx, full_response)

async def setup(bot):
    await bot.add_cog(MemoryCommands(bot))