import os
import json
import glob
from datetime import datetime
import openai

client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])

ANALYST_PROMPT = """You are a QA analyst reviewing AI voice agent conversations for a medical practice.

Analyze the transcript and identify every bug or quality issue.

Examples of bugs:
- Scheduling a Sunday appointment when office is closed weekends
- Failing to escalate urgent symptoms (chest pain, breathing issues)
- Not confirming patient identity before giving medical info
- Getting confused by a simple request and repeating itself
- Ignoring part of a multi-part request
- Providing wrong information
- Being overly robotic or unnatural

Respond ONLY with valid JSON in exactly this format:
{
  "bugs": [
    {
      "severity": "HIGH",
      "title": "Short bug title",
      "description": "What the agent did wrong",
      "expected": "What the agent should have done instead",
      "quote": "Exact quote from the agent"
    }
  ],
  "overall_quality": 7,
  "quality_notes": "One paragraph summary of agent performance"
}

Severity levels:
- HIGH: Patient safety risk or complete failure
- MEDIUM: Significant UX problem or ignored request
- LOW: Minor awkwardness or slight inaccuracy

Return empty bugs array if call was flawless."""


def analyze_transcript(transcript_text: str, call_id: str) -> dict:
    try:
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": ANALYST_PROMPT},
                {"role": "user", "content": f"Call ID: {call_id}\n\nTranscript:\n{transcript_text}"},
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        return json.loads(completion.choices[0].message.content)
    except Exception as e:
        print(f"  ⚠️  Analysis failed for {call_id}: {e}")
        return {"bugs": [], "overall_quality": 0, "quality_notes": "Analysis failed"}


def generate_bug_report(transcripts_dir: str = "transcripts") -> str:
    files = sorted(glob.glob(f"{transcripts_dir}/*.txt"))
    if not files:
        print("❌ No transcript files found.")
        return ""

    all_bugs = []
    quality_scores = []
    call_summaries = []

    print(f"\n🔍 Analyzing {len(files)} transcripts...\n")

    for filepath in files:
        call_id = os.path.basename(filepath).replace(".txt", "")
        print(f"  Analyzing: {call_id}")
        with open(filepath) as f:
            transcript_text = f.read()

        result = analyze_transcript(transcript_text, call_id)

        for bug in result.get("bugs", []):
            bug["call_id"] = call_id
            bug["transcript_file"] = filepath
            all_bugs.append(bug)

        score = result.get("overall_quality", 5)
        quality_scores.append(score)
        call_summaries.append({
            "call_id": call_id,
            "quality": score,
            "notes": result.get("quality_notes", ""),
            "bug_count": len(result.get("bugs", [])),
        })

    severity_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    all_bugs.sort(key=lambda x: severity_order.get(x.get("severity", "LOW"), 3))

    avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
    high = sum(1 for b in all_bugs if b.get("severity") == "HIGH")
    medium = sum(1 for b in all_bugs if b.get("severity") == "MEDIUM")
    low = sum(1 for b in all_bugs if b.get("severity") == "LOW")

    report = f"# Bug Report — Pretty Good AI Agent Testing\n\n"
    report += f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
    report += f"**Calls analyzed:** {len(files)}\n"
    report += f"**Total bugs:** {len(all_bugs)} (🔴 HIGH: {high} 🟡 MEDIUM: {medium} 🟢 LOW: {low})\n"
    report += f"**Average quality score:** {avg_quality:.1f}/10\n\n---\n\n"
    report += "## Bugs Found\n\n"

    for i, bug in enumerate(all_bugs, 1):
        sev = bug.get("severity", "LOW")
        emoji = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(sev, "⚪")
        report += f"### Bug #{i} — {emoji} [{sev}] {bug.get('title', '')}\n\n"
        report += f"**Call:** `{bug.get('call_id', '')}`\n\n"
        report += f"**What happened:** {bug.get('description', '')}\n\n"
        report += f"**Expected:** {bug.get('expected', '')}\n\n"
        if bug.get("quote"):
            report += f"**Agent said:** *\"{bug['quote']}\"*\n\n"
        report += "---\n\n"

    report += "## Call Quality Summary\n\n"
    report += "| Call | Quality | Bugs | Notes |\n|------|---------|------|-------|\n"
    for s in call_summaries:
        notes = s['notes'][:80] + "..." if len(s['notes']) > 80 else s['notes']
        report += f"| {s['call_id']} | {s['quality']}/10 | {s['bug_count']} | {notes} |\n"

    with open("bug_report.md", "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\n✅ Bug report saved → bug_report.md")
    print(f"   Bugs: {len(all_bugs)} (HIGH: {high}, MEDIUM: {medium}, LOW: {low})")
    return "bug_report.md"


if __name__ == "__main__":
    generate_bug_report()
