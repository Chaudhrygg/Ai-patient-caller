import os
import time
from twilio.rest import Client

TARGET_NUMBER = "+18054398008"


def make_call(scenario_id: int, server_url: str) -> str:
    client = Client(
        os.environ["TWILIO_ACCOUNT_SID"],
        os.environ["TWILIO_AUTH_TOKEN"],
    )

    call = client.calls.create(
        to=TARGET_NUMBER,
        from_=os.environ["TWILIO_PHONE_NUMBER"],
        url=f"{server_url}/voice/answer?scenario={scenario_id}",
        record=True,
        recording_status_callback=f"{server_url}/voice/recording",
        recording_status_callback_method="POST",
    )

    print(f"  📞 Call SID: {call.sid}")
    return call.sid
