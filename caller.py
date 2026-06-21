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
    )

    print(f"  📞 Call SID: {call.sid}")
    return call.sid


def run_all_scenarios(server_url: str, delay_between_calls: int = 180):
    from scenarios import SCENARIOS
    total = len(SCENARIOS)
    print(f"\n🚀 Starting {total} calls to {TARGET_NUMBER}")
    sids = []
    for scenario in SCENARIOS:
        sid = scenario["id"]
        name = scenario["name"]
        print(f"\n[{sid + 1}/{total}] Scenario: {name}")
        call_sid = make_call(sid, server_url)
        sids.append(call_sid)
        if sid < total - 1:
            print(f"  ⏳ Waiting {delay_between_calls}s...")
            time.sleep(delay_between_calls)
    print(f"\n✅ All {total} calls initiated.")
    return sids
