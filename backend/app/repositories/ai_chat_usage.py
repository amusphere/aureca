from datetime import datetime
from typing import Optional

from app.schema import AIChatUsageLog
from sqlmodel import Session, select
from sqlalchemy import and_


def get_daily_usage(session: Session, user_id: int, usage_date: str) -> Optional[AIChatUsageLog]:
    """Get daily usage record for a specific user and date"""
    stmt = select(AIChatUsageLog).where(
        and_(
            AIChatUsageLog.user_id == user_id,
            AIChatUsageLog.usage_date == usage_date
        )
    )
    return session.exec(stmt).first()


def create_daily_usage(session: Session, user_id: int, usage_date: str, usage_count: int = 1) -> AIChatUsageLog:
    """Create a new daily usage record"""
    usage_log = AIChatUsageLog(
        user_id=user_id,
        usage_date=usage_date,
        usage_count=usage_count
    )
    session.add(usage_log)
    session.commit()
    session.refresh(usage_log)
    return usage_log


def increment_daily_usage(session: Session, user_id: int, usage_date: str) -> AIChatUsageLog:
    """Increment usage count for a specific user and date, creating record if it doesn't exist"""
    existing_usage = get_daily_usage(session, user_id, usage_date)

    if existing_usage:
        # Update existing record
        existing_usage.usage_count += 1
        existing_usage.updated_at = datetime.now().timestamp()
        session.commit()
        session.refresh(existing_usage)
        return existing_usage
    else:
        # Create new record
        return create_daily_usage(session, user_id, usage_date, usage_count=1)


def get_current_usage_count(session: Session, user_id: int, usage_date: str) -> int:
    """Get current usage count for a specific user and date"""
    usage_log = get_daily_usage(session, user_id, usage_date)
    return usage_log.usage_count if usage_log else 0


def update_usage_count(session: Session, user_id: int, usage_date: str, new_count: int) -> AIChatUsageLog:
    """Update usage count for a specific user and date"""
    existing_usage = get_daily_usage(session, user_id, usage_date)

    if existing_usage:
        existing_usage.usage_count = new_count
        existing_usage.updated_at = datetime.now().timestamp()
        session.commit()
        session.refresh(existing_usage)
        return existing_usage
    else:
        return create_daily_usage(session, user_id, usage_date, usage_count=new_count)


def get_usage_history(session: Session, user_id: int, limit: int = 30) -> list[AIChatUsageLog]:
    """Get usage history for a user, ordered by date descending"""
    stmt = (
        select(AIChatUsageLog)
        .where(AIChatUsageLog.user_id == user_id)
        .order_by(AIChatUsageLog.usage_date.desc())
        .limit(limit)
    )
    return session.exec(stmt).all()