import smtplib
import os
import random
from dotenv import load_dotenv
from astra_core.config_loader import load_config

# ✅ Load environment variables and configuration
load_dotenv()
schedule_config = load_config("schedule_config")

SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
TO_NUMBER = os.getenv("TO_NUMBER")
CARRIER = os.getenv("CARRIER")

CARRIER_GATEWAYS = {
    "att": "@txt.att.net",
    "verizon": "@vtext.com",
    "tmobile": "@tmomail.net",
    "sprint": "@messaging.sprintpcs.com",
    "uscellular": "@email.uscc.net",
    "metropcs": "@mymetropcs.com",
    "boost": "@myboostmobile.com",
    "cricket": "@sms.mycricket.com",
}

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

last_sent_state = None

def remove_non_ascii(text: str) -> str:
    """Remove non-ASCII characters to ensure compatibility with SMS gateways."""
    return ''.join(c for c in text if ord(c) < 128)

def send_sms(state: str) -> bool:
    """Send a random SMS notification when Astra transitions into a new state."""
    global last_sent_state

    if not all([SENDER_EMAIL, SENDER_PASSWORD, TO_NUMBER, CARRIER]):
        print("⚠ Missing environment variables for SMS setup!")
        return False

    if CARRIER not in CARRIER_GATEWAYS:
        print("⚠ Unsupported carrier!")
        return False

    if state == last_sent_state:
        print(f"⚠ SMS already sent for {state}, skipping duplicate notification.")
        return False

    sms_address = f"{TO_NUMBER}{CARRIER_GATEWAYS[CARRIER]}"

    # ✅ Pick a random message for the state change
    state_messages = schedule_config.get("state_change_messages", {}).get(state, [])
    message = random.choice(state_messages) if state_messages else f"Astra has changed state to {state}."

    # ✅ Ensure compatibility with SMS gateway
    clean_message = remove_non_ascii(message)
    # removing SMS as it will be turned off soon
    #try:
    #    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
    #        server.starttls()
    #        server.login(SENDER_EMAIL, SENDER_PASSWORD)
    #        server.sendmail(SENDER_EMAIL, sms_address, clean_message.encode("utf-8"))  # Ensure UTF-8 encoding
    #    print(f"✅ SMS Sent: {clean_message}")
    #    last_sent_state = state  # ✅ Update last sent state
    return True
    # except Exception as e:
    #    print(f"❌ SMS Failed: {e}")
    #    return False