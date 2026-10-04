"""Provider-neutral contract for the chat model.

Messages use the Bedrock Converse shape (`{"role", "content": [{"text"} | {"toolUse"} | {"toolResult"}]}`)
as the internal format. Another provider is supported by writing one adapter class with this interface.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from ..services.calculator_gateway import ToolSpec


@dataclass(frozen=True)
class ModelTurn:
    message: dict
    wants_tools: bool

    @property
    def text(self) -> str:
        return " ".join(b["text"] for b in self.message["content"] if "text" in b).strip()

    @property
    def tool_calls(self) -> list[dict]:
        return [b["toolUse"] for b in self.message["content"] if "toolUse" in b]


class ChatModel(Protocol):
    def converse(self, system: str, messages: list[dict], tools: list[ToolSpec]) -> ModelTurn: ...
