from datetime import datetime
import pytz
from app.config.loader import load_config

def now():
    config = load_config("schedule_config")
    tz = pytz.timezone(config.get("timezone", "UTC"))
    return datetime.now(tz)

def iso_now():
    return now().isoformat()


def temporal_constraint_line():
    """
    Low-salience instrumental time for coordination. Not identity—constraint surface only.
    Astra is not defined by the clock; she is given access to time so she does not contradict reality when time matters.
    """
    dt = now()
    return f"Current date: {dt.strftime('%Y-%m-%d')} (available for reference if needed)"
