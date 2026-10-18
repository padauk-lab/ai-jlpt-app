"""Proverb of the day: the file checks, loading, and #12 GET /proverbs/today."""

import json
import sys
from collections.abc import Iterator
from datetime import date

import pytest
from pydantic import ValidationError
from sqlalchemy import select, text

from app.api.v1.proverbs import proverb_for
from app.content import load_proverbs
from app.content.load_proverbs import ProverbFile
from app.models import Proverb
from app.plan import service
from tests.test_auth import API, auth_header, error_code, register

MY = "မြန်မာ"  # any Burmese text


def proverb(first: str, reading: str) -> dict:
    return {"ruby": [{"text": first, "reading": reading}, {"text": "はなり"}], "meaning_my": MY, "explanation_my": MY}


def make_file(*items) -> dict:
    return {"proverbs": list(items) or [proverb("継続", "けいぞく"), proverb("努力", "どりょく"), proverb("忍耐", "にんたい")]}


@pytest.fixture(autouse=True)
def clean_proverbs() -> Iterator[None]:
    yield
    from app.db import engine

    with engine.begin() as conn:
        conn.execute(text("TRUNCATE proverbs RESTART IDENTITY"))


def load(data: dict) -> tuple[int, int]:
    from app.db import SessionLocal

    with SessionLocal() as db, db.begin():
        return load_proverbs.save_proverbs(db, ProverbFile.model_validate(data))


def rows() -> list[Proverb]:
    from app.db import SessionLocal

    with SessionLocal() as db:
        return list(db.scalars(select(Proverb).order_by(Proverb.id)))


# --- File checks ---


@pytest.mark.parametrize(
    ("change", "message"),
    [
        (lambda d: d["proverbs"][0]["ruby"][0].pop("reading"), "needs a reading"),
        (lambda d: d["proverbs"][0].update(meaning_my="perseverance"), "Burmese"),
        (lambda d: d["proverbs"].append(proverb("継続", "けいぞく")), "twice"),
        (lambda d: d["proverbs"][0].update(author="unknown"), "Extra inputs"),
        (lambda d: d.update(proverbs=[]), "at least 1"),
    ],
)
def test_broken_proverb_files_are_refused(change, message):
    data = make_file()
    change(data)
    with pytest.raises(ValidationError) as caught:
        ProverbFile.model_validate(data)
    assert message in str(caught.value)


# --- Loading ---


def test_loading_again_keeps_ids_and_updates_text():
    assert load(make_file()) == (3, 0)
    before = [r.id for r in rows()]
    data = make_file()
    data["proverbs"][0]["explanation_my"] = MY + " ပြင်ဆင်ပြီး"
    load(data)
    after = rows()
    assert [r.id for r in after] == before
    assert after[0].explanation_my.endswith("ပြင်ဆင်ပြီး")


def test_removed_proverbs_are_switched_off_and_can_come_back():
    load(make_file())
    assert load(make_file(proverb("継続", "けいぞく"))) == (1, 2)
    assert [r.is_active for r in rows()] == [True, False, False]
    load(make_file())
    assert all(r.is_active for r in rows())
    assert len(rows()) == 3  # no duplicates were created


def test_command_line_check_mode_changes_nothing(tmp_path, monkeypatch, capsys):
    path = tmp_path / "proverbs.json"
    path.write_text(json.dumps(make_file(), ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["load_proverbs", "--check", str(path)])
    assert load_proverbs.main() == 0
    assert "passed the checks" in capsys.readouterr().out
    assert rows() == []
    monkeypatch.setattr(sys, "argv", ["load_proverbs", str(path)])
    assert load_proverbs.main() == 0
    assert len(rows()) == 3


# --- #12 Proverb of the day ---


def headers_for(client, email="htet@example.com", username="htetpai") -> dict[str, str]:
    return auth_header(register(client, email=email, username=username)["access_token"])


def test_same_proverb_for_everyone_on_the_same_day(client, monkeypatch):
    load(make_file())
    monkeypatch.setattr(service, "today", lambda: date(2026, 10, 18))
    first = client.get(f"{API}/proverbs/today", headers=headers_for(client)).json()
    second = client.get(f"{API}/proverbs/today", headers=headers_for(client, "b@example.com", "bbb")).json()
    assert first == second
    assert set(first) == {"id", "ruby", "meaning_my", "explanation_my"}


def test_proverb_changes_every_day_and_uses_all_of_them(client, monkeypatch):
    load(make_file())
    headers = headers_for(client)
    seen = []
    for day in (16, 17, 18):
        monkeypatch.setattr(service, "today", lambda d=day: date(2026, 10, d))
        seen.append(client.get(f"{API}/proverbs/today", headers=headers).json()["id"])
    assert sorted(seen) == [r.id for r in rows()]


def test_switched_off_proverbs_are_never_shown(client, monkeypatch):
    load(make_file())
    load(make_file(proverb("継続", "けいぞく")))
    headers = headers_for(client)
    for day in range(1, 8):
        monkeypatch.setattr(service, "today", lambda d=day: date(2026, 10, d))
        assert client.get(f"{API}/proverbs/today", headers=headers).json()["ruby"][0]["text"] == "継続"


def test_no_proverbs_yet_is_404(client):
    response = client.get(f"{API}/proverbs/today", headers=headers_for(client))
    assert response.status_code == 404
    assert error_code(response) == "not_found"


def test_needs_login(client):
    assert client.get(f"{API}/proverbs/today").status_code == 401


def test_only_one_proverb_endpoint_in_the_docs(client):
    paths = client.get("/openapi.json").json()["paths"]
    assert list(paths[f"{API}/proverbs/today"]) == ["get"]
    assert paths[f"{API}/proverbs/today"]["get"]["summary"] == "#12 Proverb of the day"


def test_rotation_is_steady():
    ids = [10, 20, 30]
    assert [proverb_for(date(2026, 1, d), ids) for d in (1, 2, 3, 4)] == [10, 20, 30, 10]
