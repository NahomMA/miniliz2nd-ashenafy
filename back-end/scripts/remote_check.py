"""Run the demo persona's conversation against a deployed API and print timings and the result.

Usage (from back-end/):  uv run python scripts/remote_check.py https://<host>
"""
import json
import sys
import time
import urllib.request

from demo_conversation import MARIA_LINES

DEMO = {"email": "demo@codelinc.app", "password": "Demo2026!"}


def call(base: str, path: str, body: dict, token: str = "") -> dict:
    headers = {"Content-Type": "application/json", **({"Authorization": f"Bearer {token}"} if token else {})}
    request = urllib.request.Request(base + path, data=json.dumps(body).encode(), headers=headers)
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def main() -> None:
    base = sys.argv[1].rstrip("/")
    token = call(base, "/auth/login", DEMO)["token"]
    turn = call(base, "/assessments", {}, token)
    for line in MARIA_LINES:
        started = time.perf_counter()
        turn = call(base, f"/assessments/{turn['id']}/chat", {"message": line}, token)
        print(f"[{time.perf_counter() - started:.1f}s] {turn['reply'][:110]}")
    result = turn["assessment"]
    print("RESULT:", {k: result[k] for k in ("total_need", "gap")} if result else "no assessment", "| term:",
          result and result["projection"]["suggested_term_years"])
    blocked = call(base, f"/assessments/{call(base, '/assessments', {}, token)['id']}/chat", {"message": "What is physics?"}, token)
    print("off-topic ->", blocked["reply"][:80])


if __name__ == "__main__":
    main()
