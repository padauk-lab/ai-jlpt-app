"""Rules from the API contract that must always hold."""

API = "/api/v1"


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_errors_use_the_contract_format(client):
    not_found = client.get(f"{API}/does-not-exist")
    assert not_found.status_code == 404
    assert not_found.json() == {"error": {"code": "not_found", "message": "Not Found"}}

    invalid = client.post(f"{API}/auth/register", json={"email": "not-an-email", "username": "htetpai", "password": "x" * 8})
    assert invalid.status_code == 422
    body = invalid.json()["error"]
    assert body["code"] == "validation_error"
    assert "email" in body["fields"]


def test_starting_a_quiz_or_mock_test_never_sends_correct_answers(client):
    for path in (f"{API}/quizzes/5/attempts", f"{API}/mock-tests/3/attempts"):
        response = client.post(path)
        assert "correct_option_id" not in response.text, path
