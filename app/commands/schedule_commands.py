# schedule_commands.py

"""
⏰ Schedule Commands
-------------------
Commands for managing Astra's automated scheduling system.

These include:
- Manual schedule triggers (dinner, play, dream)
- Schedule status and configuration
- Schedule control (start/stop)

Commands are registered automatically via `auto_register_commands(...)`.

Author: Sean Wylie
Created: 2025-01-16
"""

import json
from app.services.schedule_service import (
    manual_dinner,
    manual_playtime,
    manual_dreamtime,
    get_status,
    schedule_service
)
from app.utils.common_utils import chunk_text


async def schedule_status(ctx):
    """📊 Shows the current status of Astra's automated scheduling system."""
    status = get_status()

    config_json = json.dumps(status.get('schedule_config', {}), indent=2)
    status_text = f"""⏰ **Schedule Status**

**Active:** {'✅ Yes' if status['active'] else '❌ No'}
**Running Tasks:** {', '.join(status['running_tasks']) if status['running_tasks'] else 'None'}
**Last Updated:** {status['last_updated']}

**Schedule Config:**
```json
{config_json}
```"""

    for chunk in chunk_text(status_text, max_length=1900):
        await ctx.send(chunk)

schedule_status._is_command = True
schedule_status.category = "⏰ Schedule"


async def schedule_dinner(ctx):
    """🍽️ Manually triggers Astra's dinner time reflection cycle."""
    result = await manual_dinner(ctx.bot, ctx.channel.id)
    await ctx.send(result)

schedule_dinner._is_command = True
schedule_dinner.category = "⏰ Schedule"


async def schedule_play(ctx):
    """🎮 Manually triggers Astra's playtime exploration cycle."""
    result = await manual_playtime()
    
    if "error" in result:
        await ctx.send(result["error"])
    else:
        await ctx.send(result["discovery"])
        await ctx.send(result["reflection"])

schedule_play._is_command = True
schedule_play.category = "⏰ Schedule"


async def schedule_dream(ctx):
    """💤 Manually triggers Astra's dream reflection cycle."""
    result = await manual_dreamtime()
    await ctx.send(result)

schedule_dream._is_command = True
schedule_dream.category = "⏰ Schedule"


async def schedule_stop(ctx):
    """⏹️ Stops the automated scheduling system."""
    schedule_service.stop_automated_schedule()
    await ctx.send("⏹️ Automated schedule stopped.")

schedule_stop._is_command = True
schedule_stop.category = "⏰ Schedule"


async def schedule_start(ctx):
    """▶️ Starts the automated scheduling system."""
    if schedule_service.schedule_active:
        await ctx.send("⚠️ Schedule is already active.")
        return
    
    await schedule_service.start_automated_schedule(ctx.bot, ctx.channel.id)
    await ctx.send("▶️ Automated schedule started.")

schedule_start._is_command = True
schedule_start.category = "⏰ Schedule"