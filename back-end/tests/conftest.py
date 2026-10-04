import pytest

from app import create_app
from app.ai.base import ModelTurn
from app.config import Settings

DEMO = {"email": "demo@codelinc.app", "password": "Demo2026!"}


class FakeModel:
    """Plays back prepared turns; with none left it fails like an unreachable provider."""

    def __init__(self, *turns: ModelTurn):
        self.turns, self.seen = list(turns), []

    def converse(self, system, messages, tools):
        self.seen.append(messages)
        if not self.turns:
            raise ConnectionError("model unavailable")
        return self.turns.pop(0)


def says(text: str) -> ModelTurn:
    return ModelTurn({"role": "assistant", "content": [{"text": text}]}, wants_tools=False)


def calls(name: str, arguments: dict) -> ModelTurn:
    block = {"toolUse": {"toolUseId": "call-1", "name": name, "input": arguments}}
    return ModelTurn({"role": "assistant", "content": [block]}, wants_tools=True)


@pytest.fixture
def app():
    app = create_app(Settings(secret_key="t" * 48, database_url="sqlite:///:memory:"))
    app.extensions["chat"].model = FakeModel()
    app.extensions["chat"].scope_model = None
    return app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth(client):
    token = client.post("/auth/login", json=DEMO).get_json()["token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def script(app):
    """Queue model turns for the next requests."""

    def queue(*turns: ModelTurn) -> FakeModel:
        app.extensions["chat"].model = model = FakeModel(*turns)
        return model

    return queue
