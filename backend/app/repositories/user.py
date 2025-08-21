from sqlalchemy import select
from sqlmodel import Session

from app.schema import User


def create_user(session: Session, data: dict) -> User:
    user = User(**data)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def get_user_br_column(session: Session, sub: str, column_name: str) -> User | None:
    stmt = select(User).where(getattr(User, column_name) == sub)
    return session.exec(stmt).scalar_one_or_none()


def get_user_by_id(session: Session, user_id: int) -> User | None:
    """Get user by ID."""
    stmt = select(User).where(User.id == user_id)
    return session.exec(stmt).scalar_one_or_none()


def update_user_stripe_customer_id(session: Session, user_id: int, stripe_customer_id: str) -> User | None:
    """Update user's Stripe customer ID."""
    user = get_user_by_id(session, user_id)
    if user:
        user.stripe_customer_id = stripe_customer_id
        session.add(user)
        session.commit()
        session.refresh(user)
    return user


def delete_user(session: Session, user: User) -> None:
    session.delete(user)
    session.commit()
