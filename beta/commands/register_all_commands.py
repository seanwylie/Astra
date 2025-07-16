# register_all_commands.py

"""
🧩 Command Registry
-------------------
Automatically loads all Discord command modules (excluding utils and self),
and registers their commands via docstring-based auto-registration.

Keeps `main.py` minimal and future-proof.
"""

import os
import asyncio
import importlib.util
from discord.ext import commands
from beta.commands import help_commands
from beta.commands.utils.command_utils import auto_register_commands


def register_all_commands(bot: commands.Bot):
    """
    Registers all command modules to the provided Discord bot instance.

    Auto-loads modules in beta/commands/ except:
      - register_all_commands.py
      - files in utils/
    
    Args:
        bot (commands.Bot): The Discord bot to attach commands to.
    """
    commands_dir = os.path.dirname(__file__)
    
    print(f"🔧 Loading commands from: {commands_dir}")

    for filename in os.listdir(commands_dir):
        full_path = os.path.join(commands_dir, filename)

        if filename == "register_all_commands.py":
            continue
        if filename.startswith("utils") or os.path.isdir(full_path):
            continue
        if not filename.endswith("_commands.py"):
            continue

        module_name = f"beta.commands.{filename[:-3]}"  # strip .py
        
        try:
            spec = importlib.util.spec_from_file_location(module_name, full_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            if filename == "help_commands.py":
                module.register_commands(bot)
                print(f"✅ Registered help commands from {filename}")
            else:
                # Look for Cog classes in the module
                cog_registered = False
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) and 
                        issubclass(attr, commands.Cog) and 
                        attr != commands.Cog):
                        # Create and add the Cog to the bot
                        cog_instance = attr(bot)
                        
                        # Try different methods to register the Cog properly
                        try:
                            # Method 1: Try the synchronous add_cog if available
                            if hasattr(bot, 'add_cog'):
                                if not asyncio.iscoroutinefunction(bot.add_cog):
                                    # Synchronous version
                                    bot.add_cog(cog_instance)
                                else:
                                    # Async version - we need to manually register
                                    raise Exception("Async add_cog - using manual registration")
                            else:
                                raise Exception("No add_cog method - using manual registration")
                                
                        except Exception:
                            # Method 2: Manual registration with proper cog binding
                            try:
                                # Manually add the cog to the internal cogs dict
                                # We can't modify bot.cogs directly, so we'll use the internal _cogs
                                if hasattr(bot, '_cogs'):
                                    bot._cogs[cog_instance.qualified_name] = cog_instance
                                
                                # Add all commands from the cog with proper binding
                                for command in cog_instance.get_commands():
                                    command.cog = cog_instance
                                    bot.add_command(command)
                                    
                                # Add all listeners from the cog
                                for listener in cog_instance.get_listeners():
                                    bot.add_listener(listener[1], listener[0])
                                    
                            except Exception as manual_e:
                                # Method 3: Last resort - just add commands without cog binding
                                print(f"⚠️ Manual cog registration failed for {attr_name}: {manual_e}")
                                for command in cog_instance.get_commands():
                                    bot.add_command(command)
                        print(f"✅ Registered Cog {attr_name} from {filename}")
                        cog_registered = True
                
                # Fallback to old auto-registration for non-Cog commands
                if not cog_registered:
                    auto_register_commands(bot, module, full_path)
                    print(f"✅ Auto-registered commands from {filename}")
                
        except Exception as e:
            print(f"⚠️ Failed to load {filename}: {e}")
