import time
from uuid import UUID

from sqlmodel import Session, select

from app.schema import Subscription


def create_subscription(
    session: Session,
    user_id: int,
    stripe_subscription_id: str,
    stripe_customer_id: str,
    stripe_price_id: str,
    plan_name: str,
    status: str,
    current_period_start: float,
    current_period_end: float,
    cancel_at_period_end: bool = False,
    canceled_at: float | None = None,
    trial_start: float | None = None,
    trial_end: float | None = None,
) -> Subscription:
    """Create a new subscription"""
    subscription = Subscription(
        user_id=user_id,
        stripe_subscription_id=stripe_subscription_id,
        stripe_customer_id=stripe_customer_id,
        stripe_price_id=stripe_price_id,
        plan_name=plan_name,
        status=status,
        current_period_start=current_period_start,
        current_period_end=current_period_end,
        cancel_at_period_end=cancel_at_period_end,
        canceled_at=canceled_at,
        trial_start=trial_start,
        trial_end=trial_end,
    )
    session.add(subscription)
    session.commit()
    session.refresh(subscription)
    return subscription


def get_subscription_by_id(session: Session, subscription_id: int) -> Subscription | None:
    """Get a subscription by ID"""
    return session.get(Subscription, subscription_id)


def get_subscription_by_uuid(session: Session, uuid: str | UUID) -> Subscription | None:
    """Get a subscription by UUID"""
    stmt = select(Subscription).where(Subscription.uuid == uuid)
    return session.exec(stmt).scalar_one_or_none()


def get_subscription_by_user_id(session: Session, user_id: int) -> Subscription | None:
    """Get the most recent subscription for a user"""
    stmt = select(Subscription).where(Subscription.user_id == user_id).order_by(Subscription.created_at.desc())
    return session.exec(stmt).first()


def get_subscription_by_stripe_id(session: Session, stripe_subscription_id: str) -> Subscription | None:
    """Get a subscription by Stripe subscription ID"""
    stmt = select(Subscription).where(Subscription.stripe_subscription_id == stripe_subscription_id)
    return session.exec(stmt).scalar_one_or_none()


def get_active_subscription(session: Session, user_id: int) -> Subscription | None:
    """Get the active subscription for a user"""
    current_time = time.time()
    stmt = (
        select(Subscription)
        .where(
            Subscription.user_id == user_id,
            Subscription.status.in_(["active", "trialing"]),
            Subscription.current_period_end > current_time,
        )
        .order_by(Subscription.current_period_end.desc())
    )
    return session.exec(stmt).first()


def get_subscriptions_by_user_id(session: Session, user_id: int) -> list[Subscription]:
    """Get all subscriptions for a user, ordered by creation date (newest first)"""
    stmt = select(Subscription).where(Subscription.user_id == user_id).order_by(Subscription.created_at.desc())
    return session.exec(stmt).all()


def update_subscription(
    session: Session,
    subscription_id: int,
    stripe_price_id: str | None = None,
    plan_name: str | None = None,
    status: str | None = None,
    current_period_start: float | None = None,
    current_period_end: float | None = None,
    cancel_at_period_end: bool | None = None,
    canceled_at: float | None = None,
    trial_start: float | None = None,
    trial_end: float | None = None,
) -> Subscription:
    """Update an existing subscription"""
    subscription = get_subscription_by_id(session, subscription_id)
    if not subscription:
        raise ValueError("subscription not found")

    if stripe_price_id is not None:
        subscription.stripe_price_id = stripe_price_id
    if plan_name is not None:
        subscription.plan_name = plan_name
    if status is not None:
        subscription.status = status
    if current_period_start is not None:
        subscription.current_period_start = current_period_start
    if current_period_end is not None:
        subscription.current_period_end = current_period_end
    if cancel_at_period_end is not None:
        subscription.cancel_at_period_end = cancel_at_period_end
    if canceled_at is not None:
        subscription.canceled_at = canceled_at
    if trial_start is not None:
        subscription.trial_start = trial_start
    if trial_end is not None:
        subscription.trial_end = trial_end

    subscription.updated_at = time.time()
    session.commit()
    session.refresh(subscription)
    return subscription


def update_subscription_by_stripe_id(
    session: Session,
    stripe_subscription_id: str,
    stripe_price_id: str | None = None,
    plan_name: str | None = None,
    status: str | None = None,
    current_period_start: float | None = None,
    current_period_end: float | None = None,
    cancel_at_period_end: bool | None = None,
    canceled_at: float | None = None,
    trial_start: float | None = None,
    trial_end: float | None = None,
) -> Subscription:
    """Update an existing subscription by Stripe subscription ID"""
    subscription = get_subscription_by_stripe_id(session, stripe_subscription_id)
    if not subscription:
        raise ValueError("subscription not found")

    if stripe_price_id is not None:
        subscription.stripe_price_id = stripe_price_id
    if plan_name is not None:
        subscription.plan_name = plan_name
    if status is not None:
        subscription.status = status
    if current_period_start is not None:
        subscription.current_period_start = current_period_start
    if current_period_end is not None:
        subscription.current_period_end = current_period_end
    if cancel_at_period_end is not None:
        subscription.cancel_at_period_end = cancel_at_period_end
    if canceled_at is not None:
        subscription.canceled_at = canceled_at
    if trial_start is not None:
        subscription.trial_start = trial_start
    if trial_end is not None:
        subscription.trial_end = trial_end

    subscription.updated_at = time.time()
    session.commit()
    session.refresh(subscription)
    return subscription


def deactivate_subscription(session: Session, subscription_id: int) -> Subscription:
    """Deactivate a subscription by setting status to canceled and canceled_at timestamp"""
    subscription = get_subscription_by_id(session, subscription_id)
    if not subscription:
        raise ValueError("subscription not found")

    subscription.status = "canceled"
    subscription.canceled_at = time.time()
    subscription.updated_at = time.time()

    session.commit()
    session.refresh(subscription)
    return subscription


def deactivate_subscription_by_stripe_id(session: Session, stripe_subscription_id: str) -> Subscription:
    """Deactivate a subscription by Stripe subscription ID"""
    subscription = get_subscription_by_stripe_id(session, stripe_subscription_id)
    if not subscription:
        raise ValueError("subscription not found")

    subscription.status = "canceled"
    subscription.canceled_at = time.time()
    subscription.updated_at = time.time()

    session.commit()
    session.refresh(subscription)
    return subscription


def delete_subscription(session: Session, subscription_id: int) -> None:
    """Delete a subscription (hard delete)"""
    subscription = get_subscription_by_id(session, subscription_id)
    if not subscription:
        raise ValueError("subscription not found")

    session.delete(subscription)
    session.commit()


def delete_subscription_by_stripe_id(session: Session, stripe_subscription_id: str) -> None:
    """Delete a subscription by Stripe subscription ID (hard delete)"""
    subscription = get_subscription_by_stripe_id(session, stripe_subscription_id)
    if not subscription:
        raise ValueError("subscription not found")

    session.delete(subscription)
    session.commit()


def get_subscriptions_by_status(session: Session, status: str) -> list[Subscription]:
    """Get all subscriptions with a specific status"""
    stmt = select(Subscription).where(Subscription.status == status)
    return session.exec(stmt).all()


def get_expiring_subscriptions(session: Session, before_timestamp: float) -> list[Subscription]:
    """Get subscriptions that expire before the given timestamp"""
    stmt = (
        select(Subscription)
        .where(
            Subscription.current_period_end <= before_timestamp,
            Subscription.status.in_(["active", "trialing"]),
        )
        .order_by(Subscription.current_period_end.asc())
    )
    return session.exec(stmt).all()
