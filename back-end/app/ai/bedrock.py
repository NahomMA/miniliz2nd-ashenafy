"""Amazon Bedrock adapter (Converse API). Works with any tool-capable Bedrock model."""
from __future__ import annotations

import boto3
from botocore.config import Config

from ..services.calculator_gateway import ToolSpec
from .base import ModelTurn


class BedrockChatModel:
    def __init__(self, model_id: str, region: str, guardrail_id: str = "", guardrail_version: str = "DRAFT"):
        self._model_id, self._region = model_id, region
        self._guardrail = {"guardrailIdentifier": guardrail_id, "guardrailVersion": guardrail_version} if guardrail_id else None
        self._client = None

    @property
    def client(self):
        if self._client is None:
            config = Config(read_timeout=20, connect_timeout=5, retries={"max_attempts": 2})
            self._client = boto3.client("bedrock-runtime", region_name=self._region, config=config)
        return self._client

    def converse(self, system: str, messages: list[dict], tools: list[ToolSpec]) -> ModelTurn:
        request = {
            "modelId": self._model_id,
            "system": [{"text": system}],
            "messages": messages,
            "inferenceConfig": {"maxTokens": 700, "temperature": 0.3},
        }
        if tools:
            request["toolConfig"] = {
                "tools": [
                    {"toolSpec": {"name": t.name, "description": t.description, "inputSchema": {"json": t.input_schema}}}
                    for t in tools
                ]
            }
        if self._guardrail:
            request["guardrailConfig"] = self._guardrail
        response = self.client.converse(**request)
        return ModelTurn(response["output"]["message"], response["stopReason"] == "tool_use")
