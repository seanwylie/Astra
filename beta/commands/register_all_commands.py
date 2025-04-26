# register_all_commands.py

"""
🧩 Command Registry
-------------------
Automatically loads all Discord command modules (excluding utils and self),
and registers their commands via docstring-based auto-registration.

Keeps `main.py` minimal and future-proof.
"""

import os
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

    for filename in os.listdir(commands_dir):
        full_path = os.path.join(commands_dir, filename)

        if filename == "register_all_commands.py":
            continue
        if filename.startswith("utils") or os.path.isdir(full_path):
            continue
        if not filename.endswith("_commands.py"):
            continue

        module_name = f"beta.commands.{filename[:-3]}"  # strip .py
        spec = importlib.util.spec_from_file_location(module_name, full_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        if filename == "help_commands.py":
            module.register_commands(bot)
        else:
            auto_register_commands(bot, module, full_path)
