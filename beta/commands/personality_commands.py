# personality_commands.py

"""
🎭 Personality Commands
-----------------------
Commands for managing and interacting with Astra's different personality modes.

These commands allow users to:
- Switch between different personality modes
- View current personality information
- See personality mode history and statistics
- List available personality modes

Commands are registered automatically via `auto_register_commands(...)`.

Author: Sean Wylie
Created: 2025-01-16
"""

from beta.services.personality_service import (
    personality_service,
    switch_personality,
    get_current_personality
)
from beta.utils.send_chunked_message import send_chunked_message


async def personality_current(ctx):
    """🎭 Shows Astra's current personality mode and characteristics."""
    mode_info = personality_service.get_current_mode_info()
    
    response = f"""🎭 **Current Personality Mode**

{mode_info['emoji']} **{mode_info['name']}**
*{mode_info['description']}*

**Active Since:** {mode_info['active_since']}

**Personality Traits:**
🔍 Curiosity: {mode_info['traits']['question_frequency']:.1f}x
🚀 Exploration: {mode_info['traits']['exploration_drive']:.1f}x
🔬 Detail Focus: {mode_info['traits']['detail_focus']:.1f}x
🎨 Creativity: {mode_info['traits']['creativity']:.1f}x
🧠 Analysis: {mode_info['traits']['analytical']:.1f}x

**Preferred Topics:** {', '.join(mode_info['preferred_topics'])}"""
    
    await ctx.send(response)

personality_current._is_command = True
personality_current.category = "🎭 Personality"


async def personality_list(ctx):
    """📋 Lists all available personality modes with descriptions."""
    modes = personality_service.get_available_modes()
    
    response = "🎭 **Available Personality Modes**\n\n"
    
    current_mode = get_current_personality()
    
    for mode, description in modes.items():
        marker = "👉 " if mode == current_mode else "   "
        response += f"{marker}**{mode}**: {description}\n"
    
    response += f"\n💡 Use `!personality_set <mode>` to switch modes"
    response += f"\n🔍 Use `!personality_current` to see detailed info about current mode"
    
    await ctx.send(response)

personality_list._is_command = True
personality_list.category = "🎭 Personality"


async def personality_set(ctx, mode: str):
    """🔄 Switches Astra to a different personality mode."""
    result = switch_personality(mode.lower(), f"User command by {ctx.author}")
    
    if result["success"]:
        await ctx.send(result["message"])
        
        # Add a personality-appropriate follow-up message
        if mode.lower() == "curious":
            await ctx.send("🔍 *I'm feeling incredibly curious now! What shall we explore together?*")
        elif mode.lower() == "analytical":
            await ctx.send("🧠 *My analytical processes are now optimized. What problem shall we solve?*")
        elif mode.lower() == "creative":
            await ctx.send("🎨 *The world feels like a canvas of possibilities! What shall we create?*")
        elif mode.lower() == "mentor":
            await ctx.send("🎓 *I'm here to guide and support your learning journey. What would you like to explore?*")
        elif mode.lower() == "philosophical":
            await ctx.send("🤔 *I find myself contemplating the deeper meanings... What profound questions occupy your mind?*")
        elif mode.lower() == "balanced":
            await ctx.send("⚖️ *I feel centered and whole, ready to engage with whatever interests you most.*")
    else:
        error_msg = result["message"]
        if "available_modes" in result:
            error_msg += f"\n\n**Available modes:** {', '.join(result['available_modes'])}"
        await ctx.send(error_msg)

personality_set._is_command = True
personality_set.category = "🎭 Personality"


async def personality_history(ctx, limit: int = 5):
    """📚 Shows recent personality mode changes."""
    history = personality_service.get_mode_history(limit)
    
    if not history:
        await ctx.send("📚 No personality mode changes recorded yet.")
        return
    
    response = f"📚 **Recent Personality Changes** (Last {len(history)})\n\n"
    
    for i, entry in enumerate(reversed(history), 1):
        timestamp = entry.get("timestamp", "Unknown")
        old_mode = entry.get("old_mode", "Unknown")
        new_mode = entry.get("new_mode", "Unknown")
        reason = entry.get("reason", "No reason given")
        
        # Get emoji for modes
        old_emoji = personality_service.personality_modes.get(old_mode, {}).get("emoji", "❓")
        new_emoji = personality_service.personality_modes.get(new_mode, {}).get("emoji", "❓")
        
        response += f"**{i}.** {old_emoji} {old_mode} → {new_emoji} {new_mode}\n"
        response += f"   *{reason}* • {timestamp[:16]}\n\n"
    
    await ctx.send(response)

personality_history._is_command = True
personality_history.category = "🎭 Personality"


async def personality_stats(ctx):
    """📊 Shows personality mode usage statistics."""
    stats = personality_service.get_mode_stats()
    current_info = personality_service.get_current_mode_info()
    
    response = f"""📊 **Personality Mode Statistics**

**Current Mode:** {current_info['emoji']} {current_info['name']}
**Session Duration:** {stats['current_session_duration']}
**Total Mode Switches:** {stats['total_switches']}
**Most Used Mode:** {stats['most_used_mode']}

**Usage Breakdown:**"""
    
    if stats.get("mode_usage"):
        for mode, count in sorted(stats["mode_usage"].items(), key=lambda x: x[1], reverse=True):
            emoji = personality_service.personality_modes.get(mode, {}).get("emoji", "❓")
            percentage = (count / stats['total_switches'] * 100) if stats['total_switches'] > 0 else 0
            response += f"\n{emoji} {mode}: {count} times ({percentage:.1f}%)"
    else:
        response += "\nNo usage data available yet."
    
    await ctx.send(response)

personality_stats._is_command = True
personality_stats.category = "🎭 Personality"


async def personality_random(ctx):
    """🎲 Switches to a random personality mode for variety."""
    import random
    
    available_modes = list(personality_service.personality_modes.keys())
    current_mode = get_current_personality()
    
    # Remove current mode from options to ensure we switch
    if current_mode in available_modes:
        available_modes.remove(current_mode)
    
    if not available_modes:
        await ctx.send("🎲 Only one personality mode available!")
        return
    
    random_mode = random.choice(available_modes)
    result = switch_personality(random_mode, f"Random selection by {ctx.author}")
    
    if result["success"]:
        await ctx.send(f"🎲 {result['message']}")
        await ctx.send("*Surprise! Let's see how this feels...*")
    else:
        await ctx.send(f"🎲 Random selection failed: {result['message']}")

personality_random._is_command = True
personality_random.category = "🎭 Personality"