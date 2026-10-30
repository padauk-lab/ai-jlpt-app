"""Pass prediction (docs/api-contract.md #11 and #26, app/progress/prediction.py)."""

import pytest

from app.progress.prediction import Prediction, MockScore, predict
from tests.test_auth import API
from tests.test_mock_test import RIGHT, clock, mock, ready_user, save, start, submit  # noqa: F401  (fixtures)
from tests.test_study import content  # noqa: F401  (a fixture)


def one(lk, reading):
    return predict([MockScore(lk, reading)])


# --- The formula ---


def test_no_mock_test_yet_means_no_prediction():
    assert predict([]) is None


def test_sixty_percent_is_a_fifty_percent_chance():
    assert one(60, 60) == Prediction(50, None)


@pytest.mark.parametrize(("lk", "reading", "expected"), [(64, 64, 60), (56, 56, 40), (70, 50, 60)])
def test_each_point_moves_the_chance_by_two_and_a_half(lk, reading, expected):
    # score = 70% LK + 30% reading; (70, 50) -> 64
    assert one(lk, reading).value == expected


def test_never_a_sure_pass_or_a_sure_fail():
    assert one(100, 100).value == 95
    assert one(35, 35).value == 5  # score 35: 50 - 62.5 would be negative


def test_newer_test_weighs_sixty_percent():
    newer, older = MockScore(80, 80), MockScore(40, 40)
    assert predict([newer, older]).value == 60  # 64% -> 60


def test_sections_are_weighted_separately():
    # Reading: 0.6 x 20 + 0.4 x 60 = 36 (not low). Score: 0.7 x 70 + 0.3 x 36 = 59.8 -> 49.5 -> 50
    assert predict([MockScore(70, 20), MockScore(70, 60)]) == Prediction(50, None)


def test_only_the_latest_two_tests_count():
    a, b, old = MockScore(70, 70), MockScore(60, 60), MockScore(0, 0)
    assert predict([a, b, old]) == predict([a, b])


@pytest.mark.parametrize(
    ("lk", "reading", "warning"),
    [(90, 31, "reading_low"), (31, 100, "language_knowledge_low"), (20, 20, "both_low")],
)
def test_one_weak_section_caps_the_chance(lk, reading, warning):
    prediction = one(lk, reading)
    assert prediction.warning == warning
    assert prediction.value <= 15


def test_exactly_at_the_section_minimum_is_not_low():
    assert one(32, 90).warning is None


# --- In the app ---


def dashboard(client, headers):
    return client.get(f"{API}/dashboard", headers=headers).json()


def take_test(client, headers, mock, answers):
    attempt = start(client, headers, mock["mock"]).json()["attempt_id"]
    for number, option in answers.items():
        save(client, headers, attempt, mock["questions"][number], option)
    return submit(client, headers, attempt).json()


def test_first_attempt_sets_the_prediction_on_the_dashboard(client, mock, clock):
    headers = ready_user(client, mock)
    body = take_test(client, headers, mock, RIGHT)  # everything right
    assert (body["pass_prediction"], body["pass_prediction_warning"]) == (95, None)
    home = dashboard(client, headers)
    assert (home["pass_prediction"], home["pass_prediction_warning"]) == (95, None)


def test_a_retake_does_not_change_the_prediction(client, mock, clock):
    headers = ready_user(client, mock)
    take_test(client, headers, mock, RIGHT)
    retake = take_test(client, headers, mock, {})  # all wrong this time
    assert retake["counts_for_prediction"] is False
    assert retake["pass_prediction"] == 95
    assert dashboard(client, headers)["pass_prediction"] == 95


def test_weak_reading_shows_the_warning(client, mock, clock):
    headers = ready_user(client, mock)
    answers = {n: RIGHT[n] for n in (1, 2, 3, 4)}  # all language knowledge right, reading all wrong
    body = take_test(client, headers, mock, answers)
    assert (body["pass_prediction"], body["pass_prediction_warning"]) == (15, "reading_low")


def test_time_out_counts_too(client, mock, clock):
    headers = ready_user(client, mock)
    attempt = start(client, headers, mock["mock"]).json()["attempt_id"]
    for number, option in RIGHT.items():
        save(client, headers, attempt, mock["questions"][number], option)
    clock.move(minutes=31)  # never submitted: the server submits it at the end time
    assert dashboard(client, headers)["pass_prediction"] == 95


def test_a_new_round_starts_without_a_prediction(client, mock, clock):
    """After "reset all progress" (#37) the user is in a new round, and old tests no longer count."""
    from app.db import SessionLocal
    from app.models import User

    headers = ready_user(client, mock)
    take_test(client, headers, mock, RIGHT)
    with SessionLocal() as db, db.begin():
        db.query(User).one().current_round += 1
    assert dashboard(client, headers)["pass_prediction"] is None


def test_someone_elses_tests_do_not_count(client, mock, clock):
    take_test(client, ready_user(client, mock), mock, RIGHT)
    from tests.test_auth import auth_header, register

    other = auth_header(register(client, email="other@example.com", username="other")["access_token"])
    assert dashboard(client, other)["pass_prediction"] is None
