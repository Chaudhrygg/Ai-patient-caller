import os
from fastapi import FastAPI, Form, Request
from fastapi.responses import Response
from twilio.twiml.voice_response import VoiceResponse, Gather

from patient_ai import PatientAI
from recorder import CallRecorder

app = FastAPI()
sessions: dict = {}


def speak_and_listen(text: str, action: str) -> str:
    vr = VoiceResponse()
    gather = Gather(
        input="speech",
        action=action,
        method="POST",
        speech_timeout="auto",
        speech_model="phone_call",
        enhanced="true",
        timeout=10,
    )
    gather.pause(length=1)
    gather.say(text, voice="Polly.Joanna", language="en-US")
    vr.append(gather)
    vr.redirect(action, method="POST")
    return str(vr)


def speak_and_hangup(text: str) -> str:
    vr = VoiceResponse()
    vr.pause(length=1)
    vr.say(text, voice="Polly.Joanna", language="en-US")
    vr.pause(length=1)
    vr.hangup()
    return str(vr)


@app.post("/voice/answer")
async def voice_answer(request: Request, CallSid: str = Form(...)):
    scenario_id = int(request.query_params.get("scenario", "0"))
    ai = PatientAI(scenario_id=scenario_id)
    recorder = CallRecorder(call_sid=CallSid, scenario_name=ai.get_scenario_name())
    sessions[CallSid] = {"ai": ai, "recorder": recorder}
    opening = ai.get_opening()
    recorder.log("PATIENT", opening)
    print(f"\n📞 Call connected | SID: {CallSid} | Scenario: {ai.get_scenario_name()}")
    return Response(content=speak_and_listen(opening, "/voice/gather"), media_type="application/xml")


@app.post("/voice/gather")
async def voice_gather(
    request: Request,
    CallSid: str = Form(...),
    SpeechResult: str = Form(""),
    Confidence: str = Form("0"),
):
    session = sessions.get(CallSid)
    if not session:
        vr = VoiceResponse()
        vr.hangup()
        return Response(content=str(vr), media_type="application/xml")

    ai = session["ai"]
    recorder = session["recorder"]
    agent_text = SpeechResult.strip()

    if agent_text:
        recorder.log("AGENT", f"{agent_text} [conf={float(Confidence):.2f}]")
    else:
        recorder.log("AGENT", "[silence]")

    patient_response = ai.respond(agent_text)
    hangup = "[HANGUP]" in patient_response
    clean_response = patient_response.replace("[HANGUP]", "").strip()
    if not clean_response:
        clean_response = "Thank you so much. Goodbye!"

    recorder.log("PATIENT", clean_response)

    if hangup:
        recorder.finalize()
        sessions.pop(CallSid, None)
        return Response(content=speak_and_hangup(clean_response), media_type="application/xml")

    return Response(content=speak_and_listen(clean_response, "/voice/gather"), media_type="application/xml")


@app.post("/voice/recording")
async def recording_callback(
    CallSid: str = Form(...),
    RecordingUrl: str = Form(""),
    RecordingDuration: str = Form("0"),
):
    session = sessions.get(CallSid)
    if session and RecordingUrl:
        session["recorder"].set_recording_url(RecordingUrl)
        session["recorder"]._download_audio()
    return {"status": "ok"}


@app.post("/voice/status")
async def status_callback(
    CallSid: str = Form(...),
    CallStatus: str = Form(""),
    CallDuration: str = Form("0"),
):
    if CallStatus in ("completed", "failed", "busy", "no-answer", "canceled"):
        session = sessions.pop(CallSid, None)
        if session:
            print(f"  📊 Call ended | Status: {CallStatus} | Duration: {CallDuration}s")
            session["recorder"].finalize()
    return {"status": "ok"}


@app.get("/health")
def health():
    return {"status": "ok", "active_calls": len(sessions)}
