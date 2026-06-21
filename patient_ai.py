import openai
import os
from scenarios import SCENARIOS

client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])

SYSTEM_TEMPLATE = """You are a real patient calling a medical office on the phone.

PERSONA: {persona}
SITUATION: {description}
YOUR GOAL: {goal}

STRICT RULES:
1. Max 2 sentences per response — you're on the phone
2. Sound natural: hesitate, use "um", vary your phrasing
3. Stay in character — never break it
4. React genuinely to mistakes: confusion, frustration, pushback
5. If goal is fully done, wrap up and say [HANGUP] at the end
6. If agent gives wrong info (e.g. books you Sunday), react with surprise
7. If stuck in loop 2+ times with zero progress, get frustrated, say [HANGUP]
8. Do NOT ask multiple questions at once — one thing at a time"""


class PatientAI:
    def __init__(self, scenario_id: int):
        self.scenario = SCENARIOS[scenario_id % len(SCENARIOS)]
        self.history = []
        self.turn_count = 0
        self.max_turns = 12
        self.stuck_count = 0
        self.last_agent_50 = ""
        self._system = SYSTEM_TEMPLATE.format(
            persona=self.scenario["persona"],
            description=self.scenario["description"],
            goal=self.scenario["goal"],
        )

    def get_opening(self) -> str:
        return self.scenario["opening"]

    def respond(self, agent_speech: str) -> str:
        self.turn_count += 1
        if self.turn_count >= self.max_turns:
            return "Okay I think I have what I need. Thank you. Goodbye! [HANGUP]"

        snippet = agent_speech[:50] if agent_speech else ""
        if snippet and snippet == self.last_agent_50:
            self.stuck_count += 1
        else:
            self.stuck_count = 0
            self.last_agent_50 = snippet

        if self.stuck_count >= 2:
            return "I'm not getting anywhere. I'll call back. Goodbye. [HANGUP]"

        recent_history = self.history[-8:]
        recent_history.append({"role": "user", "content": agent_speech or "[silence]"})

        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": self._system}] + recent_history,
            max_tokens=80,
            temperature=0.85,
        )

        response = completion.choices[0].message.content.strip()
        self.history.append({"role": "user", "content": agent_speech or ""})
        self.history.append({"role": "assistant", "content": response})
        return response

    def get_scenario_name(self) -> str:
        return self.scenario["name"]

    def get_turn_count(self) -> int:
        return self.turn_count
