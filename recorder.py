import os
import time
import requests
from datetime import datetime


class CallRecorder:
    def __init__(self, call_sid: str, scenario_name: str = "unknown"):
        self.call_sid = call_sid
        self.scenario_name = scenario_name
        self.transcript = []
        self.recording_url = None
        self.start_time = datetime.now()
        self.duration_turns = 0
        os.makedirs("transcripts", exist_ok=True)
        os.makedirs("recordings", exist_ok=True)

    def log(self, speaker: str, text: str):
        timestamp = datetime.now().strftime("%M:%S")
        entry = {"speaker": speaker, "text": text, "timestamp": timestamp}
        self.transcript.append(entry)
        if speaker == "AGENT":
            self.duration_turns += 1
        print(f"  [{timestamp}] {speaker}: {text}")

    def set_recording_url(self, url: str):
        self.recording_url = url

    def finalize(self):
        path = self._save_transcript()
        if self.recording_url:
            self._download_audio()
        return path

    def _save_transcript(self) -> str:
        filename = f"transcripts/{self.scenario_name}_{self.call_sid}.txt"
        elapsed = (datetime.now() - self.start_time).seconds
        with open(filename, "w") as f:
            f.write(f"Call SID: {self.call_sid}\n")
            f.write(f"Scenario: {self.scenario_name}\n")
            f.write(f"Date: {self.start_time.isoformat()}\n")
            f.write(f"Duration: ~{elapsed}s | Agent turns: {self.duration_turns}\n")
            f.write("=" * 60 + "\n\n")
            for entry in self.transcript:
                f.write(f"[{entry['timestamp']}] {entry['speaker']}: {entry['text']}\n")
        print(f"  ✅ Transcript saved → {filename}")
        return filename

    def _download_audio(self):
        auth = (
            os.environ["TWILIO_ACCOUNT_SID"],
            os.environ["TWILIO_AUTH_TOKEN"],
        )
        formats = [
            (self.recording_url + ".ogg", f"recordings/{self.scenario_name}_{self.call_sid}.ogg"),
            (self.recording_url + ".mp3", f"recordings/{self.scenario_name}_{self.call_sid}.mp3"),
        ]
        for attempt in range(4):
            time.sleep(8)
            for url, filename in formats:
                try:
                    r = requests.get(url, auth=auth, timeout=30)
                    if r.status_code == 200 and len(r.content) > 1000:
                        with open(filename, "wb") as f:
                            f.write(r.content)
                        print(f"  ✅ Audio saved → {filename}")
                        return
                except Exception as e:
                    print(f"  ⚠️  Attempt {attempt + 1}: {e}")
        print(f"  ❌ Could not download audio for {self.call_sid}")
