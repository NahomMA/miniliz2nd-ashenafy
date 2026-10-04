"""Run the demo persona's conversation against the real model and print each turn.

Usage (from back-end/):  uv run python scripts/demo_conversation.py
"""
import dataclasses
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app  # noqa: E402
from app.config import Settings  # noqa: E402

MARIA_LINES = [
    "I'm 34 and I have two kids, 3 and 6.",
    "I make about 85 thousand a year.",
    "We owe 240k on the house with 25 years left, and about 15k on a car.",
    "Yes, I'd like to cover college. We have around 30k saved.",
    "I have 50k through work.",
]


def main() -> None:
    settings = dataclasses.replace(Settings.from_env(), database_url="sqlite:///:memory:")
    app = create_app(settings)
    app.extensions["chat"].warm_up()
    client = app.test_client()
    token = client.post("/auth/login", json={"email": settings.demo_email, "password": settings.demo_password}).get_json()["token"]
    headers = {"Authorization": f"Bearer {token}"}
    turn = client.post("/assessments", headers=headers).get_json()
    print(f"model: {settings.bedrock_model_id}\nAI:   {turn['reply']}\n")
    for line in MARIA_LINES:
        start = time.perf_counter()
        turn = client.post(f"/assessments/{turn['id']}/chat", json={"message": line}, headers=headers).get_json()
        print(f"USER: {line}\nAI:   {turn['reply']}   [{time.perf_counter() - start:.1f}s]\n")
    result = turn["assessment"]
    print("RESULT:", {k: result[k] for k in ("total_need", "resources", "gap")} if result else "no assessment yet")
    if result:
        print("TERM:", result["projection"]["suggested_term_years"], "| PROFILE:", turn["profile"])


if __name__ == "__main__":
    main()
