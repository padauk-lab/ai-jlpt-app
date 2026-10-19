"""#16 to #18: saved words (bookmarks), including attempts to save locked words or touch other users' lists."""

import pytest
from sqlalchemy import func, select

from app.models import Bookmark, Word
from tests.test_auth import API, auth_header, error_code, register
from tests.test_study import RUBY, content, user_header  # noqa: F401  (content is a fixture)


def save(client, headers, word_id):
    return client.post(f"{API}/bookmarks", json={"word_id": word_id}, headers=headers)


def saved(client, headers, search=None) -> dict:
    params = {"search": search} if search is not None else None
    response = client.get(f"{API}/bookmarks", params=params, headers=headers)
    assert response.status_code == 200, response.text
    return response.json()


def count_rows() -> int:
    from app.db import SessionLocal

    with SessionLocal() as db:
        return db.scalar(select(func.count()).select_from(Bookmark))


@pytest.fixture
def locked_word(content):
    """A word in unit 2, which is locked for a new user."""
    from app.db import SessionLocal

    with SessionLocal() as db, db.begin():
        word = Word(unit_id=content["units"][2], position=1, word="抑制", furigana="よくせい", ruby=RUBY, meaning_my="ထိန်းချုပ်ခြင်း")
        db.add(word)
        db.flush()
        return word.id


# --- #17 Save ---


def test_save_a_word_and_see_it_in_the_list(client, content):
    headers = user_header(client)
    response = save(client, headers, content["word1"])
    assert response.status_code == 201
    assert response.json() == {"word_id": content["word1"], "bookmarked": True}

    body = saved(client, headers)
    assert body["total"] == 1
    word = body["words"][0]
    assert word["word_id"] == content["word1"]
    assert word["ruby"] == RUBY
    assert word["meaning_my"] == "m1"
    assert (word["session_number"], word["unit_number"]) == (1, 1)
    assert word["saved_at"].endswith("Z")


def test_saving_twice_is_safe(client, content):
    headers = user_header(client)
    assert save(client, headers, content["word1"]).status_code == 201
    assert save(client, headers, content["word1"]).status_code == 201
    assert count_rows() == 1


def test_words_in_locked_units_cannot_be_saved(client, content, locked_word):
    headers = user_header(client)
    response = save(client, headers, locked_word)
    assert response.status_code == 403
    assert error_code(response) == "unit_locked"
    assert count_rows() == 0


def test_unknown_word_is_404(client, content):
    response = save(client, user_header(client), 999999)
    assert response.status_code == 404


@pytest.mark.parametrize("bad", [0, -1, "1", True, 1.5, None, 10**20])
def test_bad_word_ids_are_refused(client, content, bad):
    response = client.post(f"{API}/bookmarks", json={"word_id": bad}, headers=user_header(client))
    assert response.status_code == 422


def test_extra_fields_are_refused(client, content):
    body = {"word_id": content["word1"], "user_id": 999}
    response = client.post(f"{API}/bookmarks", json=body, headers=user_header(client))
    assert response.status_code == 422


# --- #16 List ---


def test_newest_first(client, content):
    headers = user_header(client)
    save(client, headers, content["word1"])
    save(client, headers, content["word2"])
    assert [w["word_id"] for w in saved(client, headers)["words"]] == [content["word2"], content["word1"]]


def test_each_user_sees_only_their_own_list(client, content):
    first = user_header(client)
    save(client, first, content["word1"])
    second = auth_header(register(client, email="other@example.com", username="other")["access_token"])
    assert saved(client, second) == {"total": 0, "words": []}


@pytest.mark.parametrize(
    ("search", "expected"),
    [
        ("w1", ["word1"]),  # the word
        ("x", ["word1", "word2"]),  # the reading (both test words read "x")
        ("m2", ["word2"]),  # the Burmese meaning
        ("  w2  ", ["word2"]),  # spaces around are ignored
        ("", ["word1", "word2"]),  # empty search = everything
        ("%", []),  # % is a normal letter, not "match everything"
        ("_", []),  # _ is a normal letter too
        ("'; DROP TABLE bookmarks;--", []),  # SQL injection does nothing
    ],
)
def test_search(client, content, search, expected):
    headers = user_header(client)
    save(client, headers, content["word1"])
    save(client, headers, content["word2"])
    found = {w["word_id"] for w in saved(client, headers, search)["words"]}
    assert found == {content[name] for name in expected}
    assert count_rows() == 2


def test_search_is_limited_to_50_characters(client, content):
    response = client.get(f"{API}/bookmarks", params={"search": "a" * 51}, headers=user_header(client))
    assert response.status_code == 422


def test_saved_words_survive_a_progress_reset(client, content):
    headers = user_header(client)
    client.post(f"{API}/onboarding", json={"last_level": "not_taken"}, headers=headers)
    save(client, headers, content["word1"])
    assert client.post(f"{API}/me/reset-progress", json={"confirm": "RESET"}, headers=headers).status_code == 200
    assert saved(client, headers)["total"] == 1


# --- #18 Remove ---


def test_remove_a_saved_word(client, content):
    headers = user_header(client)
    save(client, headers, content["word1"])
    assert client.delete(f"{API}/bookmarks/{content['word1']}", headers=headers).status_code == 204
    assert saved(client, headers)["total"] == 0
    second_time = client.delete(f"{API}/bookmarks/{content['word1']}", headers=headers)
    assert second_time.status_code == 404


def test_cannot_remove_another_users_saved_word(client, content):
    first = user_header(client)
    save(client, first, content["word1"])
    second = auth_header(register(client, email="other@example.com", username="other")["access_token"])
    assert client.delete(f"{API}/bookmarks/{content['word1']}", headers=second).status_code == 404
    assert saved(client, first)["total"] == 1


# --- Login ---


def test_saved_words_need_login(client, content):
    assert client.get(f"{API}/bookmarks").status_code == 401
    assert client.post(f"{API}/bookmarks", json={"word_id": content["word1"]}).status_code == 401
    assert client.delete(f"{API}/bookmarks/{content['word1']}").status_code == 401
