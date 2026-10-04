from datetime import datetime, timedelta, timezone

from tests.conftest import DEMO
from tests.test_calculator import MARIA

NEW_USER = {"email": "Sam@Example.com ", "password": "correct-horse", "name": "Sam"}


def error(response):
    return response.get_json()["error"]


def test_health_is_public(client):
    assert client.get("/health").get_json() == {"ok": True}


def test_register_returns_session_and_normalizes_email(client):
    r = client.post("/auth/register", json=NEW_USER)
    assert r.status_code == 201
    body = r.get_json()
    assert body["user"]["email"] == "sam@example.com" and body["token"]
    assert "password" not in str(body)


def test_register_rejects_duplicate_email(client):
    client.post("/auth/register", json=NEW_USER)
    r = client.post("/auth/register", json=NEW_USER)
    assert (r.status_code, error(r)["code"]) == (409, "email_taken")


def test_register_validates_input(client):
    for patch, field in [({"email": "nope"}, "email"), ({"password": "short"}, "password"), ({"name": ""}, "name")]:
        r = client.post("/auth/register", json={**NEW_USER, **patch})
        assert (r.status_code, error(r)["field"]) == (400, field)
    assert client.post("/auth/register", data="not json").status_code == 400


def test_login_success_and_me(client, auth):
    assert client.get("/auth/me", headers=auth).get_json()["user"]["email"] == DEMO["email"]


def test_login_failures_are_indistinguishable(client):
    wrong_password = client.post("/auth/login", json={**DEMO, "password": "wrong-password"})
    unknown_email = client.post("/auth/login", json={"email": "nobody@example.com", "password": "wrong-password"})
    assert wrong_password.status_code == unknown_email.status_code == 401
    assert error(wrong_password) == error(unknown_email)


def test_protected_route_rejects_missing_bad_and_expired_tokens(app, client):
    expired = app.extensions["tokens"].issue(1, now=datetime.now(timezone.utc) - timedelta(days=2))
    for headers in ({}, {"Authorization": "Bearer garbage"}, {"Authorization": f"Bearer {expired}"}):
        r = client.get("/auth/me", headers=headers)
        assert (r.status_code, error(r)["code"]) == (401, "invalid_token")


def test_assess_returns_full_assessment(client, auth):
    r = client.post("/calculator/assess", json={"profile": MARIA}, headers=auth)
    body = r.get_json()
    assert r.status_code == 200
    assert (body["total_need"], body["gap"], body["projection"]["suggested_term_years"]) == (1_633_900, 1_553_900, 20)


def test_assess_requires_auth_and_valid_profile(client, auth):
    assert client.post("/calculator/assess", json={"profile": MARIA}).status_code == 401
    r = client.post("/calculator/assess", json={"profile": {**MARIA, "age": 5}}, headers=auth)
    assert (r.status_code, error(r)["field"]) == (400, "age")


def test_unknown_route_returns_json_error(client):
    r = client.get("/nope")
    assert (r.status_code, error(r)["code"]) == (404, "not_found")
