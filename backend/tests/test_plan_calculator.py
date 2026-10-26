"""Study plan math. Pure calculations, so these tests need no login and no data."""

from datetime import date

from app.plan.calculator import DEFAULT_UNITS_PER_DAY, MAX_UNITS_PER_DAY, calculate_plan

TODAY = date(2026, 10, 14)
EXAM = date(2026, 12, 6)  # 53 days later


def test_no_exam_date_uses_the_default_pace():
    plan = calculate_plan(TODAY, None, "N2", units_done=0)
    assert plan.units_per_day == DEFAULT_UNITS_PER_DAY
    assert plan.days_left is None and plan.finish_by is None


def test_finishes_before_the_exam_with_review_days_left():
    plan = calculate_plan(TODAY, EXAM, "N2", units_done=0)
    assert plan.days_left == 53
    assert plan.units_per_day == 3  # 100 units in 39 study days, rounded up
    assert plan.finish_by == date(2026, 11, 16)
    assert (EXAM - plan.finish_by).days >= 14  # two weeks free for review


def test_n1_takers_get_fewer_review_days_so_a_lighter_pace():
    soon = date(2026, 11, 17)  # 34 days: N1 gets 27 study days (4 a day), others 23 (5 a day)
    n1 = calculate_plan(TODAY, soon, "N1", units_done=0)
    first_time = calculate_plan(TODAY, soon, "not_taken", units_done=0)
    assert n1.units_per_day < first_time.units_per_day


def test_progress_already_made_lowers_the_pace():
    fresh = calculate_plan(TODAY, EXAM, "N2", units_done=0)
    halfway = calculate_plan(TODAY, EXAM, "N2", units_done=50)
    assert halfway.units_per_day < fresh.units_per_day


def test_pace_never_goes_above_the_maximum():
    plan = calculate_plan(TODAY, date(2026, 10, 15), "N2", units_done=0)
    assert plan.units_per_day == MAX_UNITS_PER_DAY


def test_exam_today_or_passed_does_not_crash():
    for exam in (TODAY, date(2026, 1, 1)):
        plan = calculate_plan(TODAY, exam, "N1", units_done=0)
        assert plan.days_left == 0
        assert 1 <= plan.units_per_day <= MAX_UNITS_PER_DAY


def test_everything_done():
    plan = calculate_plan(TODAY, EXAM, "N1", units_done=100)
    assert plan.units_per_day == 1  # the database requires at least 1
    assert plan.finish_by == TODAY


def test_pace_is_always_at_least_one_for_far_away_exams():
    plan = calculate_plan(TODAY, date(2027, 12, 5), "not_taken", units_done=0)
    assert plan.units_per_day == 1
    assert plan.finish_by < date(2027, 12, 5)
