"""Daily study reminder: a push notification at the time the user chose in Settings (#31, #32).

Rules:
- Only users with daily_reminder on (on by default), onboarding finished, and a registered phone (#33).
- Sent at the user's reminder_time in the user's own timezone. If the server was busy or asleep at that
  minute, it still goes out up to 30 minutes late, but never later (no reminder at 2 a.m.).
- At most one reminder per user per day, even with several servers running (the notification_log table).
- No reminder if the user already studied that day (finished a unit, or started a quiz or mock test).

Run once by hand (for testing): python -m app.notifications.reminders
"""

import logging
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import delete, exists, func, or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models import Device, MockAttempt, NotificationLog, NotificationSettings, QuizAttempt, UnitProgress, User
from app.notifications.push import PushMessage, is_expo_token, send_push

logger = logging.getLogger(__name__)

KIND = "daily_reminder"
LATE_WINDOW = timedelta(minutes=30)
KEEP_LOG_DAYS = 7
PUSH_PLATFORMS = ("ios", "android")  # Expo can't push to "web"

TITLE = "急合"
BODY = "ဒီနေ့ လေ့လာချိန် ရောက်ပါပြီ။ ခဏလေးဖြစ်ဖြစ် ဆက်လေ့လာကြရအောင်။"

# The same defaults as GET /me/notifications (#31) for users who never changed their settings.
DEFAULT_TIME = time(20, 0)
DEFAULT_TIMEZONE = "Asia/Tokyo"


def due_day(now: datetime, timezone: str, reminder_time: time) -> date | None:
    """The user's day whose reminder is due right now, or None.

    Looks at today and yesterday, so a 23:50 reminder still goes out at 00:10.
    """
    try:
        zone = ZoneInfo(timezone)
    except (ZoneInfoNotFoundError, ValueError):
        zone = ZoneInfo(DEFAULT_TIMEZONE)
    local_now = now.astimezone(zone)
    for day in (local_now.date(), local_now.date() - timedelta(days=1)):
        at = datetime.combine(day, reminder_time, tzinfo=zone)
        if at <= local_now < at + LATE_WINDOW:
            return day
    return None


def _studied_since(db: Session, user_id: int, since: datetime) -> bool:
    return bool(db.scalar(select(or_(
        exists().where(UnitProgress.user_id == user_id, UnitProgress.completed_at >= since),
        exists().where(QuizAttempt.user_id == user_id, QuizAttempt.started_at >= since),
        exists().where(MockAttempt.user_id == user_id, MockAttempt.started_at >= since),
    ))))


def send_due_reminders(db: Session, now: datetime | None = None) -> int:
    """Send every reminder that is due now. Returns how many users got one."""
    now = now or datetime.now(UTC)

    has_phone = exists().where(Device.user_id == User.id, Device.platform.in_(PUSH_PLATFORMS))
    candidates = db.execute(
        select(
            User.id,
            func.coalesce(NotificationSettings.reminder_time, DEFAULT_TIME),
            func.coalesce(NotificationSettings.timezone, DEFAULT_TIMEZONE),
        )
        .outerjoin(NotificationSettings, NotificationSettings.user_id == User.id)
        .where(User.onboarding_completed.is_(True), func.coalesce(NotificationSettings.daily_reminder, True), has_phone)
    ).all()

    reminded: list[int] = []
    for user_id, reminder_time, timezone in candidates:
        day = due_day(now, timezone, reminder_time)
        if day is None:
            continue
        start_of_day = datetime.combine(day, time(0, 0), tzinfo=ZoneInfo(timezone))
        if _studied_since(db, user_id, start_of_day):
            continue
        # Claim the reminder first. If another server already claimed it, nothing is added and we skip.
        claimed = db.scalar(
            insert(NotificationLog)
            .values(user_id=user_id, kind=KIND, local_date=day)
            .on_conflict_do_nothing()
            .returning(NotificationLog.user_id)
        )
        if claimed is not None:
            reminded.append(user_id)

    db.execute(delete(NotificationLog).where(NotificationLog.local_date < now.date() - timedelta(days=KEEP_LOG_DAYS)))
    db.commit()  # claims are saved before sending, so a reminder is never sent twice

    if not reminded:
        return 0
    tokens = db.scalars(
        select(Device.push_token).where(Device.user_id.in_(reminded), Device.platform.in_(PUSH_PLATFORMS))
    ).all()
    messages = [PushMessage(to=t, title=TITLE, body=BODY, data={"type": KIND}) for t in tokens if is_expo_token(t)]
    db.close()  # no database connection is held while waiting for Expo

    dead = send_push(messages)
    if dead:
        db.execute(delete(Device).where(Device.push_token.in_(dead)))
        db.commit()
        logger.info("Removed %d phone(s) that can no longer get notifications", len(dead))
    return len(reminded)


if __name__ == "__main__":
    from app.db import SessionLocal

    logging.basicConfig(level=logging.INFO)
    with SessionLocal() as session:
        print(f"Reminders sent: {send_due_reminders(session)}")
