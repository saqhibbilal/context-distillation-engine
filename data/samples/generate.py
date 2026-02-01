"""
Generate simulated Discord-style chat logs for demos.
Run: python generate.py
"""

import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

SAMPLES_DIR = Path(__file__).parent

# Templates for different scenarios
HACKATHON = [
    ("Alex", "Alright team, we have 24 hours. What's our MVP scope?"),
    ("Sam", "I think auth + one core feature. Login and the main flow."),
    ("Jordan", "+1. I'll handle the frontend, React + Vite."),
    ("Alex", "Sam - backend API? Jordan - can you also do the deploy config?"),
    ("Sam", "On it. I'll use FastAPI. Database - SQLite for speed?"),
    ("Jordan", "Sure. I'll add a Dockerfile. We can deploy to Railway."),
    ("Riley", "lol just saw the prize pool"),
    ("Alex", "Focus people. Decision: SQLite, FastAPI backend, React frontend. Jordan owns deploy."),
    ("Jordan", "Roger. Open question: do we need a staging env or ship straight to prod?"),
    ("Sam", "Ship to prod. No time for staging. We can add env vars for config."),
]

STUDY_GROUP = [
    ("Mia", "Can we push the session to 3pm? Got a conflict."),
    ("Omar", "Works for me. Same room?"),
    ("Ella", "Yes, room 204. We're covering chapters 5-7 right?"),
    ("Mia", "Yes. I'll prepare the summary for chapter 5."),
    ("Omar", "I'll do chapter 6. Ella - can you handle 7?"),
    ("Ella", "Sure. Should we do practice problems after?"),
    ("Mia", "Good idea. Decision: 3pm, room 204, each does one chapter summary + practice."),
    ("Omar", "Reminder: exam is next Tuesday. We should do a mock before."),
]

STARTUP_CHANNEL = [
    ("Devon", "Deployment failed again. The env vars aren't loading in prod."),
    ("Casey", "Check the Railway dashboard - they might be scoped to the wrong service."),
    ("Devon", "Found it. Was pointing to staging. Fixed."),
    ("Taylor", "Heads up: we're hitting rate limits on the external API. Need to add caching."),
    ("Casey", "I'll add Redis. Can have it done by EOD."),
    ("Devon", "Taylor - can you document the API contract? Casey - Redis + cache key strategy."),
    ("Taylor", "Will do. Open question: do we deprecate the v1 endpoint this sprint?"),
    ("Casey", "I vote yes. We've migrated all clients. Decision: deprecate v1 end of week."),
]


def _format_line(author: str, content: str, base_time: datetime) -> str:
    t = base_time + timedelta(minutes=random.randint(0, 30))
    return f"[{t.strftime('%Y-%m-%d %H:%M')}] {author}: {content}"


def generate(scenario: str, base_date: Optional[datetime] = None) -> str:
    base = base_date or datetime.now().replace(hour=10, minute=0, second=0, microsecond=0)
    if scenario == "hackathon":
        lines = HACKATHON
    elif scenario == "study":
        lines = STUDY_GROUP
    elif scenario == "startup":
        lines = STARTUP_CHANNEL
    else:
        raise ValueError(f"Unknown scenario: {scenario}")
    return "\n".join(_format_line(a, c, base) for a, c in lines)


def main():
    SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
    base = datetime(2024, 1, 15, 10, 0, 0)
    for name, scenario in [("hackathon", "hackathon"), ("study_group", "study"), ("startup_channel", "startup")]:
        path = SAMPLES_DIR / f"{name}.txt"
        path.write_text(generate(scenario, base), encoding="utf-8")
        print(f"Wrote {path}")
    print("Done. Use these files for paste/upload demos.")


if __name__ == "__main__":
    main()
