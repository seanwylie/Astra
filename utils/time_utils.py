from datetime import datetime
import pytz
from astra_core.config_loader import load_config

def now():
    config = load_config("schedule_config")
    tz = pytz.timezone(config.get("timezone", "UTC"))
    return datetime.now(tz)

def iso_now():
    return now().isoformat()
