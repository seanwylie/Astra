# schedule_service.py

"""
⏰ Schedule Service
------------------
Integrates Astra's scheduling system (dinner, dream, play cycles) into the beta architecture.

This service wraps the astra_schedule module to provide:
- Automated scheduling execution
- Manual schedule triggers
- Schedule state management
- Background task coordination

Author: Sean Wylie
Created: 2025-01-16
"""

import asyncio
from typing import Optional, Dict, Any
from datetime import datetime

# Core scheduling imports
from astra_core.astra_schedule.schedule import astra_schedule
from astra_core.astra_schedule.dinner import start_dinner_time
from astra_core.astra_schedule.play import creative_thinking, spark_opinion
from astra_core.astra_schedule.dream import process_dream_seed
# Note: schedule_state module doesn't have get/update functions
# We'll implement basic state tracking here

# Configuration
from beta.config.beta_config import config_manager


class ScheduleService:
    """
    Service for managing Astra's automated and manual scheduling.
    """
    
    def __init__(self):
        self.schedule_config = config_manager.get_schedule_config()
        self.running_tasks = {}
        self.schedule_active = False
    
    async def start_automated_schedule(self, bot, channel_id: int):
        """
        Start the automated schedule system.
        
        Args:
            bot: Discord bot instance
            channel_id: Channel ID for schedule notifications
        """
        if self.schedule_active:
            print("⚠️ Schedule already active")
            return
        
        self.schedule_active = True
        print("⏰ Starting automated Astra schedule...")
        
        # Start the main schedule task
        schedule_task = asyncio.create_task(
            astra_schedule(bot, channel_id)
        )
        self.running_tasks['main_schedule'] = schedule_task
        
        return schedule_task
    
    def stop_automated_schedule(self):
        """Stop the automated schedule system."""
        self.schedule_active = False
        
        for task_name, task in self.running_tasks.items():
            if not task.done():
                task.cancel()
                print(f"⏰ Cancelled schedule task: {task_name}")
        
        self.running_tasks.clear()
        print("⏰ Automated schedule stopped")
    
    async def trigger_dinner_manually(self, bot, channel_id: int) -> str:
        """
        Manually trigger Astra's dinner time.
        
        Args:
            bot: Discord bot instance
            channel_id: Channel ID to send dinner messages
            
        Returns:
            Status message
        """
        try:
            await start_dinner_time(bot, channel_id)
            return "🍽️ Dinner time initiated successfully"
        except Exception as e:
            return f"❌ Failed to start dinner time: {e}"
    
    async def trigger_playtime_manually(self) -> Dict[str, str]:
        """
        Manually trigger Astra's playtime cycle.
        
        Returns:
            Dictionary with discovery and reflection
        """
        try:
            concept = await creative_thinking(return_concept=True)
            opinion = await spark_opinion(concept)
            
            return {
                "discovery": f"🧠 Astra discovered:\n{concept}",
                "reflection": f"🌟 Astra reflects:\n{opinion}"
            }
        except Exception as e:
            return {
                "error": f"❌ Failed to execute playtime: {e}"
            }
    
    async def trigger_dreamtime_manually(self) -> str:
        """
        Manually trigger Astra's dream cycle.
        
        Returns:
            Status message
        """
        try:
            await process_dream_seed()
            return "💤 Dream cycle completed successfully"
        except Exception as e:
            return f"❌ Failed to execute dream cycle: {e}"
    
    def get_schedule_status(self) -> Dict[str, Any]:
        """
        Get current schedule status and state.
        
        Returns:
            Dictionary with schedule information
        """
        return {
            "active": self.schedule_active,
            "running_tasks": list(self.running_tasks.keys()),
            "schedule_config": self.schedule_config,
            "last_updated": datetime.now().isoformat()
        }
    
    def update_schedule_configuration(self, new_config: Dict[str, Any]) -> bool:
        """
        Update schedule configuration.
        
        Args:
            new_config: New configuration values
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Update the configuration
            self.schedule_config.update(new_config)
            
            # If schedule is running, restart with new config
            if self.schedule_active:
                print("⏰ Restarting schedule with new configuration...")
                # Note: This would require bot and channel_id to be stored
                # For now, just update the config
            
            return True
        except Exception as e:
            print(f"❌ Failed to update schedule configuration: {e}")
            return False


# Global schedule service instance
schedule_service = ScheduleService()


# Convenience functions for backward compatibility
async def start_schedule(bot, channel_id: int):
    """Start the automated schedule."""
    return await schedule_service.start_automated_schedule(bot, channel_id)


def stop_schedule():
    """Stop the automated schedule."""
    schedule_service.stop_automated_schedule()


async def manual_dinner(bot, channel_id: int) -> str:
    """Manually trigger dinner time."""
    return await schedule_service.trigger_dinner_manually(bot, channel_id)


async def manual_playtime() -> Dict[str, str]:
    """Manually trigger playtime."""
    return await schedule_service.trigger_playtime_manually()


async def manual_dreamtime() -> str:
    """Manually trigger dreamtime."""
    return await schedule_service.trigger_dreamtime_manually()


def get_status() -> Dict[str, Any]:
    """Get schedule status."""
    return schedule_service.get_schedule_status()