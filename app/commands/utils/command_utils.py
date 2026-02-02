import os
import re
from discord.ext.commands import Command


def extract_doc_category(path):
    """
    Extracts the category label from the module's top docstring.

    Args:
        path (str): Path to the module file.

    Returns:
        str: Category label like "🧠 Emotional Commands" or None if not found.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
            match = re.search(r'"""[\s\S]*?^([^\n]*?Commands)\n[-=]{3,}', content, re.MULTILINE)
            if match:
                return match.group(1).strip()
    except Exception:
        return None


def auto_register_commands(bot, command_module, module_path):
    """
    Registers all command functions in a module and tags them with category
    extracted from that module’s docstring.

    Args:
        bot (commands.Bot): The bot instance to register to.
        command_module (module): The imported Python module containing commands.
        module_path (str): The file path to that module (used for docstring parsing).
    """
    category = extract_doc_category(module_path) or "🧩 Miscellaneous"
    for attr in dir(command_module):
        maybe_func = getattr(command_module, attr)
        if callable(maybe_func) and getattr(maybe_func, "_is_command", False):
            cmd = Command(maybe_func, name=maybe_func.__name__, help=maybe_func.__doc__ or "")
            cmd.category = category
            bot.add_command(cmd)


def load_category_order_from_docs(commands_path=None):
    """
    Scans all command modules and extracts their emoji-labeled category headers from docstrings.

    Returns:
        List[str]: Ordered list of category headers like ["🌱 Spark", "🧠 Emotional"]
    """
    if commands_path is None:
        commands_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # app/commands
    categories = []
    for filename in os.listdir(commands_path):
        if filename.endswith("_commands.py"):
            full_path = os.path.join(commands_path, filename)
            category = extract_doc_category(full_path)
            if category and category not in categories:
                categories.append(category)
    return categories
