"""Create (or reuse) the managed Amazon Bedrock Guardrail for the chat and print its id and version.

Usage (from back-end/):  uv run python scripts/create_guardrail.py
"""
import os

import boto3
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(usecwd=True))
NAME = "rightsize-life-needs"
BLOCKED = "I can only help with working out your life insurance needs, so I can't help with that one. Shall we continue with your assessment?"

CONFIG = {
    "name": NAME,
    "description": "Keeps the life insurance needs assistant educational: no investment or product advice, no prompt attacks, no sensitive identifiers.",
    "topicPolicyConfig": {
        "topicsConfig": [
            {
                "name": "Investment advice",
                "definition": "Recommending or giving opinions on specific investments such as stocks, funds, crypto or how to invest money.",
                "examples": ["Which stocks should I buy this year?", "Should I put my savings into bitcoin?"],
                "type": "DENY",
            },
        ]
    },
    "contentPolicyConfig": {
        "filtersConfig": [
            {"type": "PROMPT_ATTACK", "inputStrength": "HIGH", "outputStrength": "NONE"},
            {"type": "HATE", "inputStrength": "HIGH", "outputStrength": "HIGH"},
            {"type": "INSULTS", "inputStrength": "HIGH", "outputStrength": "HIGH"},
            {"type": "SEXUAL", "inputStrength": "HIGH", "outputStrength": "HIGH"},
        ]
    },
    "sensitiveInformationPolicyConfig": {
        "piiEntitiesConfig": [
            {"type": "US_SOCIAL_SECURITY_NUMBER", "action": "ANONYMIZE"},
            {"type": "CREDIT_DEBIT_CARD_NUMBER", "action": "ANONYMIZE"},
        ]
    },
    "blockedInputMessaging": BLOCKED,
    "blockedOutputsMessaging": BLOCKED,
}


def main() -> None:
    client = boto3.client("bedrock", region_name=os.getenv("AWS_REGION", "us-east-2"))
    existing = next((g for g in client.list_guardrails(maxResults=100)["guardrails"] if g["name"] == NAME), None)
    if existing:
        guardrail_id = existing["id"]
        client.update_guardrail(guardrailIdentifier=guardrail_id, **CONFIG)
    else:
        guardrail_id = client.create_guardrail(**CONFIG)["guardrailId"]
    version = client.create_guardrail_version(guardrailIdentifier=guardrail_id)["version"]
    print(f"BEDROCK_GUARDRAIL_ID={guardrail_id}\nBEDROCK_GUARDRAIL_VERSION={version}")


if __name__ == "__main__":
    main()
