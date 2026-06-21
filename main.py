import argparse
import subprocess
import sys
import os
import time

from caller import make_call
from bug_analyzer import generate_bug_report
from scenarios import SCENARIOS


def check_env():
    required = [
        "TWILIO_ACCOUNT_SID",
        "TWILIO_AUTH_TOKEN",
        "TWILIO_PHONE_NUMBER",
        "OPENAI_API_KEY",
        "NGROK_URL",
    ]
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        print(f"❌ Missing env vars: {', '.join(missing)}")
        sys.exit(1)


def start_server() -> subprocess.Popen:
    print("🌐 Starting FastAPI server on :8000...")
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "server:app",
         "--host", "0.0.0.0", "--port", "8000", "--log-level", "warning"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    time.sleep(3)
    print("   ✅ Server ready\n")
    return proc


def run_batch(scenario_ids: list, server_url: str, delay: int):
    total = len(scenario_ids)
    for i, sid in enumerate(scenario_ids):
        name = SCENARIOS[sid]["name"]
        print(f"[{i+1}/{total}] Scenario {sid}: {name}")
        make_call(sid, server_url)
        if i < total - 1:
            print(f"  ⏳ Waiting {delay}s...\n")
            time.sleep(delay)


def main():
    parser = argparse.ArgumentParser(description="Pretty Good AI Voice Bot")
    parser.add_argument("--scenario", type=int, default=-1)
    parser.add_argument("--batch", type=int, choices=[1, 2])
    parser.add_argument("--report-only", action="store_true")
    parser.add_argument("--delay", type=int, default=180)
    args = parser.parse_args()

    check_env()
    server_url = os.environ["NGROK_URL"].rstrip("/")

    if args.report_only:
        generate_bug_report()
        return

    server_proc = start_server()

    try:
        if args.scenario >= 0:
            name = SCENARIOS[args.scenario % len(SCENARIOS)]["name"]
            print(f"📞 Single call | Scenario {args.scenario}: {name}")
            make_call(args.scenario, server_url)
            print(f"⏳ Waiting {args.delay}s...")
            time.sleep(args.delay)

        elif args.batch == 1:
            print("📞 BATCH 1 — Scenarios 0-5\n")
            run_batch(list(range(6)), server_url, args.delay)
            print("\n✅ Batch 1 done.")
            print("👉 Listen to recordings/, then run: python main.py --batch 2\n")

        elif args.batch == 2:
            print("📞 BATCH 2 — Scenarios 6-11\n")
            run_batch(list(range(6, 12)), server_url, args.delay)
            print("\n✅ Batch 2 done. Generating bug report...")
            time.sleep(5)
            generate_bug_report()

        else:
            print("📞 Running all 12 scenarios...\n")
            run_batch(list(range(12)), server_url, args.delay)
            print("\n✅ All done. Generating bug report...")
            time.sleep(5)
            generate_bug_report()

    finally:
        server_proc.terminate()
        print("👋 Server stopped.")


if __name__ == "__main__":
    main()
