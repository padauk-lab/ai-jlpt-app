"""sessions: number 1 to 10

The app has 10 sessions (#76). The database rule said 1 to 20; now it says 1 to 10.
Safe to run: no session above 10 can exist, because the content rules refuse them.

Revision ID: a7c3e9d2b415
Revises: e5a39863d70b
Create Date: 2026-11-04 11:00:00.000000

"""

from collections.abc import Sequence

from alembic import op


# Revision identifiers, used by Alembic.
revision: str = 'a7c3e9d2b415'
down_revision: str | Sequence[str] | None = 'e5a39863d70b'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint(op.f('ck_sessions_number_range'), 'sessions', type_='check')
    op.create_check_constraint(op.f('ck_sessions_number_range'), 'sessions', 'number BETWEEN 1 AND 10')


def downgrade() -> None:
    op.drop_constraint(op.f('ck_sessions_number_range'), 'sessions', type_='check')
    op.create_check_constraint(op.f('ck_sessions_number_range'), 'sessions', 'number BETWEEN 1 AND 20')
