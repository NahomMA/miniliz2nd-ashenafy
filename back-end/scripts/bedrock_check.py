"""Smoke test: confirm the Bedrock token works and report which Claude models respond.

Usage (from back-end/):  uv run python scripts/bedrock_check.py
"""
import os
import time

import boto3
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(usecwd=True))
REGION = os.getenv("AWS_REGION", "us-east-2")
FALLBACK = [
    "us.amazon.nova-pro-v1:0",
    "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
    "us.anthropic.claude-haiku-4-5-20251001-v1:0",
]


def candidates() -> list[str]:
    if model := os.getenv("BEDROCK_MODEL_ID"):
        return [model]
    try:
        profiles = boto3.client("bedrock", region_name=REGION).list_inference_profiles(maxResults=200)
        ids = [p["inferenceProfileId"] for p in profiles["inferenceProfileSummaries"]]
        return sorted(i for i in ids if "anthropic.claude" in i) or FALLBACK
    except Exception as exc:
        print(f"(could not list inference profiles: {type(exc).__name__}; trying known IDs)")
        return FALLBACK


def main() -> None:
    if not os.getenv("AWS_BEARER_TOKEN_BEDROCK"):
        raise SystemExit("AWS_BEARER_TOKEN_BEDROCK is not set")
    client = boto3.client("bedrock-runtime", region_name=REGION)
    print(f"region={REGION}")
    for model in candidates():
        start = time.perf_counter()
        try:
            resp = client.converse(
                modelId=model,
                messages=[{"role": "user", "content": [{"text": "Reply with the single word: ready"}]}],
                inferenceConfig={"maxTokens": 10},
            )
            text = resp["output"]["message"]["content"][0]["text"].strip()
            print(f"OK    {model}  {time.perf_counter() - start:.1f}s  -> {text}")
        except Exception as exc:
            print(f"FAIL  {model}  {type(exc).__name__}: {str(exc)[:90]}")


if __name__ == "__main__":
    main()
