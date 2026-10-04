import pytest

from app.ai import guardrails
from app.ai.scripted import ScriptedInterview
from tests.conftest import calls, says
from tests.test_calculator import MARIA

NEW_USER = {"email": "other@example.com", "password": "correct-horse", "name": "Other"}


@pytest.fixture
def chat(client, auth):
    started = client.post("/assessments", headers=auth)
    assert started.status_code == 201
    url = f"/assessments/{started.get_json()['id']}"
    send = lambda text: client.post(f"{url}/chat", json={"message": text}, headers=auth).get_json()
    send.url, send.greeting = url, started.get_json()["reply"]
    return send


def test_start_greets_by_first_name_without_calling_the_model(chat):
    assert chat.greeting.startswith("Hi Maria,")


def test_model_conversation_produces_the_assessment(chat, script):
    script(says("Thanks. About how much do you earn in a year?"))
    first = chat("I'm 34 with two kids, 3 and 6")
    assert (first["done"], first["assessment"]) == (False, None)

    model = script(calls("full_assessment", {"profile": MARIA}), says("Your coverage goal is $1,633,900, and you already have $80,000."))
    final = chat("85k, mortgage 240k with 25 years left, 15k car loan, 30k saved, 50k through work")
    assert final["done"] and final["reply"].startswith("Your coverage goal is $1,633,900")
    assert (final["assessment"]["total_need"], final["assessment"]["gap"]) == (1_633_900, 1_553_900)
    assert final["profile"]["annual_income"] == 85_000
    tool_result = model.seen[1][-1]["content"][0]["toolResult"]["content"][0]["json"]
    assert tool_result["total_need"] == 1_633_900


def test_invented_amounts_are_replaced_with_the_calculated_explanation(chat, script):
    script(calls("full_assessment", {"profile": MARIA}), says("You need roughly $2 million in coverage."))
    reply = chat("everything at once")["reply"]
    assert "$2 million" not in reply and "$1,633,900" in reply


def test_falls_back_to_scripted_interview_when_the_model_fails(chat, client, auth):
    assert "How old are you?" in chat("hello")["reply"]
    answers = ["34", "3 and 6", "about 85k", "$240,000", "25", "15k on a car", "around 30k", "50k through work"]
    for text in answers:
        turn = chat(text)
    assert turn["done"] and "$1,633,900" in turn["reply"]
    assert (turn["assessment"]["gap"], turn["assessment"]["projection"]["suggested_term_years"]) == (1_553_900, 20)
    saved = client.get(chat.url, headers=auth).get_json()
    assert saved["assessment"]["total_need"] == 1_633_900 and len(saved["messages"]) == 1 + 2 * 9
    assert client.get("/assessments", headers=auth).get_json()["items"][0]["total_need"] == 1_633_900


def test_scripted_interview_handles_none_not_sure_and_retries():
    interview, state = ScriptedInterview(), ScriptedInterview.new_state()
    state, question = interview.answer(state, "not sure")
    assert question.startswith("Could you give me a number") and state["step"] == 0
    for text in ("40", "none", "60000", "no mortgage", "not sure", "none", "none"):
        state, question = interview.answer(state, text)
    assert question is None
    assert state["answers"] == {"age": 40, "dependents": [], "annual_income": 60_000, "mortgage_balance": 0, "savings": 0, "existing_coverage": 0}


def test_ssn_is_redacted_before_storage_and_before_the_model(chat, script, client, auth):
    model = script(says("That is not needed. How old are you?"))
    chat("my ssn is 123-45-6789")
    assert "123-45-6789" not in str(model.seen)
    assert "123-45-6789" not in str(client.get(chat.url, headers=auth).get_json())


def test_chat_validates_message_and_ownership(chat, client, auth):
    assert client.post(f"{chat.url}/chat", json={}, headers=auth).status_code == 400
    assert client.post(f"{chat.url}/chat", json={"message": "x" * 1001}, headers=auth).status_code == 400
    assert client.post(f"{chat.url}/chat", json={"message": "hi"}).status_code == 401
    other = {"Authorization": f"Bearer {client.post('/auth/register', json=NEW_USER).get_json()['token']}"}
    assert client.get(chat.url, headers=other).status_code == 404
    assert client.post(f"{chat.url}/chat", json={"message": "hi"}, headers=other).status_code == 404
    assert client.get("/assessments", headers=other).get_json() == {"items": []}


def test_amount_parsing_and_output_check():
    assert guardrails.parse_amounts("85k, $240,000 and 1.2 million") == [85_000, 240_000, 1_200_000]
    assert guardrails.visible("<thinking> plan </thinking>\n\nHow old are you?") == "How old are you?"
    assert guardrails.numbers_in({"a": [1, {"b": 2}], "c": True, "d": "3"}) == {1, 2}
    assert guardrails.unsupported_amounts("goal $1,633,900, not $5k", {1_633_900}) == ["$5k"]


def test_off_topic_message_is_blocked_before_the_main_model(app, chat, script, client, auth):
    model = script(says("should never be used"))
    app.extensions["chat"].scope_model = type(model)(says("OUT"))
    reply = chat("What is physics?")["reply"]
    assert reply.startswith("I can only help with working out your life insurance needs")
    assert reply.endswith("who depends on you financially?")
    assert model.seen == []
    assert "physics" not in str(app.extensions["chat"].model.seen)


def test_in_scope_message_and_failed_scope_check_both_reach_the_main_model(app, chat, script):
    script(says("Thanks. What is your yearly income?"), says("And do you have a mortgage?"))
    app.extensions["chat"].scope_model = type(app.extensions["chat"].model)(says("IN"))
    assert chat("I'm 34 with two kids")["reply"] == "Thanks. What is your yearly income?"
    assert chat("85k")["reply"] == "And do you have a mortgage?"


def test_last_question_extraction():
    assert guardrails.last_question("Thanks, Maria. Noted! Do you have a mortgage? If so, how much is left?") == "If so, how much is left?"
    assert guardrails.last_question("No question here.") == ""
