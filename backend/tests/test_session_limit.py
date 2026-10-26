"""The app has 10 sessions (2,000 words). Content files for session 11 or later are refused."""

import pytest
from pydantic import ValidationError

from app.api.v1.dashboard import SESSIONS_TOTAL
from app.content.mock_schema import MockTestFile
from app.content.quiz_schema import QuizFile
from app.content.schema import UnitFile
from app.plan.calculator import UNITS_TOTAL
from app.progress.unlock import UNITS_PER_SESSION
from tests.test_load_mock_tests import make_mock
from tests.test_load_mock_tests import make_unit as mock_unit
from tests.test_load_quizzes import make_quiz


def test_totals_agree():
    assert SESSIONS_TOTAL == 10
    assert UNITS_TOTAL == SESSIONS_TOTAL * UNITS_PER_SESSION


@pytest.mark.parametrize(
    ("schema", "make"),
    [(UnitFile, lambda: mock_unit(1)), (QuizFile, make_quiz), (MockTestFile, make_mock)],
)
def test_session_10_is_the_last(schema, make):
    data = make()
    data["session_number"] = 10
    schema.model_validate(data)  # fine

    data["session_number"] = 11
    with pytest.raises(ValidationError):
        schema.model_validate(data)
