# sms_helper.py

"""
📵 SMS Helper (Disabled)
------------------------
This module previously sent SMS notifications when Astra entered a new state.
SMS is now fully disabled and the sending logic has been removed.

If re-enabled in the future, reintroduce SMTP or Twilio integration here.
"""

def send_sms(state: str) -> bool:
    """Stubbed SMS function. Currently disabled."""
    print(f"📵 [send_sms] Called with state='{state}', but SMS functionality is disabled.")
    return False
