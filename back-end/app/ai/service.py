"""Conversation orchestration: the model talks, MCP tools calculate, the model explains."""
from __future__ import annotations

import logging

from ..models import Assessment, User
from ..services.calculator_gateway import CalculatorGateway
from . import guardrails
from .base import ChatModel
from .prompts import CLARIFY, CRISIS_REPLY, GREETING, OFF_TOPIC_REPLY, RESUME, RESUME_GENERIC, SCOPE_PROMPT, SYSTEM_PROMPT
from .scripted import ADULT_AGES, ADULTS_ONLY, INTRO, ScriptedInterview, summarize

log = logging.getLogger(__name__)
FOLLOW_UP = (
    "You're all set. Your results are on the results screen, where you can explore and adjust the numbers. "
    "Ask me anything about them."
)


class ChatService:
    MAX_TOOL_ROUNDS = 4
    SCOPE_CHECK_MIN_WORDS = 3  # one- and two-word replies are answers; the main model's own rules still apply

    def __init__(self, model: ChatModel, calculator: CalculatorGateway, scope_model: ChatModel | None = None):
        self.model, self.calculator, self.scope_model = model, calculator, scope_model
        self._interview = ScriptedInterview()

    def warm_up(self) -> None:
        """Pay one-time costs (MCP tool list, AWS client) at startup instead of on the first message."""
        try:
            self.calculator.tools()
            getattr(self.model, "client", None)
        except Exception:
            log.warning("Warm-up failed; the first message will be slower", exc_info=True)

    def start(self, user: User) -> Assessment:
        greeting = GREETING.format(name=user.name.split()[0])
        return Assessment(user_id=user.id, transcript=[{"role": "assistant", "text": greeting}])

    def reply(self, assessment: Assessment, message: str) -> str:
        """Handle one user message, update the assessment in place and return the assistant's reply."""
        message = guardrails.redact(message)
        assessment.transcript = [*assessment.transcript, {"role": "user", "text": message}]
        if guardrails.mentions_self_harm(message):
            reply = CRISIS_REPLY  # fixed, supportive reply; never sent to the model or the calculator
        elif assessment.mode == Assessment.AI:
            try:
                reply = self._model_turn(assessment, message)
            except Exception:
                log.exception("Model unavailable; continuing assessment %s with the scripted interview", assessment.id)
                assessment.mode, assessment.state = Assessment.SCRIPTED, self._interview.new_state()
                reply = INTRO + self._interview.question(assessment.state)
        else:
            reply = self._scripted_turn(assessment, message)
        assessment.transcript = [*assessment.transcript, {"role": "assistant", "text": reply}]
        return reply

    def _model_turn(self, assessment: Assessment, message: str) -> str:
        last_reply = assessment.transcript[-2]["text"]
        if assessment.done and len(message.split()) < self.SCOPE_CHECK_MIN_WORDS:
            return FOLLOW_UP  # a greeting or thanks after the result must not restart the interview
        age = guardrails.stated_age(message)
        if age is not None and age not in ADULT_AGES and not assessment.done:
            return ADULTS_ONLY  # decided in code so the interview never continues for a minor
        if not self._in_scope(last_reply, message):
            question = guardrails.last_question(last_reply)
            return OFF_TOPIC_REPLY + (RESUME + question if question else RESUME_GENERIC)
        messages = [*assessment.llm_messages, {"role": "user", "content": [{"text": message}]}]
        tools, profile, result = self.calculator.tools(), None, None
        turn = self.model.converse(SYSTEM_PROMPT, messages, tools)
        for _ in range(self.MAX_TOOL_ROUNDS):
            if not turn.wants_tools:
                break
            results = []
            for call in turn.tool_calls:
                output = self.calculator.call(call["name"], call["input"])
                if "error" not in output and isinstance(call["input"].get("profile"), dict):
                    profile = {**call["input"]["profile"], **call["input"].get("changes", {})}
                    result = output if call["name"] == "full_assessment" else None
                results.append({"toolResult": {"toolUseId": call["toolUseId"], "content": [{"json": output}]}})
            messages += [turn.message, {"role": "user", "content": results}]
            turn = self.model.converse(SYSTEM_PROMPT, messages, tools)
        if turn.wants_tools:
            raise RuntimeError("model did not finish within the tool round limit")

        assessment.llm_messages = [*messages, turn.message]
        if profile is not None:
            self._complete(assessment, profile, result)
        return self._checked(assessment, turn.text)

    def _in_scope(self, last_reply: str, message: str) -> bool:
        """Input guardrail: a small, fast model decides whether the message belongs in this chat.

        Off-topic messages never reach the main model or its history. If the check itself fails,
        the message is let through; the main model's own scope rules still apply.
        """
        if self.scope_model is None or len(message.split()) < self.SCOPE_CHECK_MIN_WORDS:
            return True
        prompt = f"Assistant asked: {last_reply}\n\nUser replied: {message}"
        try:
            verdict = self.scope_model.converse(SCOPE_PROMPT, [{"role": "user", "content": [{"text": prompt}]}], [])
        except Exception:
            log.warning("Scope check unavailable; passing the message to the main model", exc_info=True)
            return True
        in_scope = not guardrails.visible(verdict.text).upper().startswith("OUT")
        if not in_scope:
            log.info("Off-topic message blocked by the scope check")
        return in_scope

    def _scripted_turn(self, assessment: Assessment, message: str) -> str:
        if assessment.done:
            return FOLLOW_UP
        assessment.state, question = self._interview.answer(assessment.state, message)
        if question:
            return question
        if result := self._complete(assessment, assessment.state["answers"]):
            return summarize(result)
        assessment.state = self._interview.new_state()
        return "Something in those answers did not add up. Let's try again. " + self._interview.question(assessment.state)

    def _complete(self, assessment: Assessment, profile: dict, result: dict | None = None) -> dict | None:
        """Store the full assessment, calculating it unless the model already did. None if the profile is invalid."""
        result = result or self.calculator.call("full_assessment", {"profile": profile})
        if "error" in result:
            return None
        assessment.profile, assessment.result = profile, result
        return result

    def _checked(self, assessment: Assessment, reply: str) -> str:
        """Output guardrail: every dollar amount must come from a tool result or from the user."""
        reply = guardrails.visible(reply)
        said_by_user = {n for t in assessment.transcript if t["role"] == "user" for n in guardrails.parse_amounts(t["text"])}
        tool_numbers = guardrails.numbers_in(assessment.llm_messages)
        if invented := guardrails.unsupported_amounts(reply, said_by_user | tool_numbers):
            log.warning("Reply contained unsupported amounts %s; replaced with the templated explanation", invented)
            return summarize(assessment.result) if assessment.result else "Thanks. Could you tell me a little more so I can work this out properly?"
        return reply or (FOLLOW_UP if assessment.result else CLARIFY)
