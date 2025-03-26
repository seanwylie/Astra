import json
import os
import builtins
import inspect
import logging
from logging.handlers import RotatingFileHandler

# ✅ Log Directory
LOG_DIR = os.path.expanduser("~/astra_logs")
os.makedirs(LOG_DIR, exist_ok=True)

# ✅ Log Rotation Settings
LOG_MAX_SIZE = 5 * 1024 * 1024  # 5MB per log file
LOG_BACKUP_COUNT = 5  # Keep 5 rotated log files

# ✅ Define log files
LOG_FILES = {
    "general": os.path.join(LOG_DIR, "astra.log"),
    "processing": os.path.join(LOG_DIR, "astra_processing.log"),
    "discord": os.path.join(LOG_DIR, "astra_discord.log"),
}

# ✅ Create separate loggers for each file
loggers = {}
for log_name, log_file in LOG_FILES.items():
    handler = RotatingFileHandler(log_file, maxBytes=LOG_MAX_SIZE, backupCount=LOG_BACKUP_COUNT)
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))

    logger = logging.getLogger(log_name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)

    loggers[log_name] = logger

loggers["general"].info("✅ Log rotation is active for all log files.")

# ✅ Override `print` to use general logger
original_print = builtins.print

def custom_print(*args, **kwargs):
    """Override print to include filename and log to appropriate log file."""
    frame = inspect.currentframe().f_back
    filename = os.path.basename(frame.f_code.co_filename)
    log_message = f"[{filename}] " + " ".join(map(str, args))

    # Default to general log
    loggers["general"].info(log_message)
    original_print(log_message)

builtins.print = custom_print  # 🚀 Apply global override

# ✅ Debugging Functions
def debug_log(action: str, log_type: str = "general"):
    """Prints a debug statement with the function name automatically."""
    caller_function = inspect.stack()[1].function
    log_message = f"📥 [DEBUG] {action} Mind in {caller_function}..."
    loggers[log_type].info(log_message)
    print(log_message)

# ✅ Config Directory Setup
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))  # Moves up from utils/
ASTRA_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))  # Moves up to project root
CONFIG_DIR = os.getenv("ASTRA_CONFIG_DIR", os.path.join(ASTRA_DIR, "config"))

print(f"Config directory: {CONFIG_DIR}")

CONFIG_CACHE = {}

# ✅ Config Loading Functions
def load_config(filename: str) -> dict:
    """Load a JSON config file dynamically, ensuring it always appends `.json`."""
    if not filename.endswith(".json"):
        filename += ".json"  # Ensure file has the `.json` extension

    file_path = os.path.join(CONFIG_DIR, filename)

    print(f"Loading config file from: {file_path}")

    if filename in CONFIG_CACHE:
        return CONFIG_CACHE[filename]  # Return cached version if already loaded

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            CONFIG_CACHE[filename] = json.load(f)  # Store in cache for faster access
            return CONFIG_CACHE[filename]
    except FileNotFoundError:
        print(f"⚠ Warning: {filename} not found in {CONFIG_DIR}. Using defaults.")
    except json.JSONDecodeError:
        print(f"❌ Error: {filename} is corrupted. Using defaults.")

    CONFIG_CACHE[filename] = {}  # Prevent repeated failures
    return CONFIG_CACHE[filename]

def get_config(key: str, default=None, config_file: str = "general_config.json"):
    """Retrieve a key from a given config file, ensuring it exists."""
    config = load_config(config_file)

    if key not in config:
        print(f"⚠ Warning: Missing key '{key}' in {config_file}. Using default: {default}")

    return config.get(key, os.getenv(key.upper(), default))  # Uses env fallback if missing
