#!/usr/bin/env python3

import sys
sys.path.append('/Users/shuto/src/amusphere/aureca/backend')

from sqlmodel import Session, create_engine, select
from sqlalchemy import case
from app.schema import Tasks, TaskPriority, User

# Create in-memory SQLite database
engine = create_engine("sqlite:///:memory:", echo=True)  # echo=True to see SQL
Tasks.metadata.create_all(engine)

with Session(engine) as session:
    # Create test user
    user = User(
        name="Test User",
        email="test@example.com",
        created_at=1672531200.0,
        updated_at=1672531200.0,
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    # Create test tasks
    tasks_data = [
        ("High Priority Task", TaskPriority.HIGH, 1672617600.0),
        ("Middle Priority Task", TaskPriority.MIDDLE, 1672704000.0),
        ("Low Priority Task", TaskPriority.LOW, 1672790400.0),
        ("No Priority Task", None, 1672876800.0),
    ]

    for title, priority, expires_at in tasks_data:
        task = Tasks(
            user_id=user.id,
            title=title,
            description=f"Description for {title}",
            priority=priority,
            completed=False,
            expires_at=expires_at,
            created_at=1672531200.0,
            updated_at=1672531200.0,
        )
        session.add(task)
    session.commit()

    print("=== Test: Direct query with CASE ===")

    # Reproduce the same query as in find_tasks
    stmt = select(Tasks).where(
        Tasks.user_id == user.id,
        Tasks.completed.is_(False),  # Use is_(False) instead of == False
    )

    priority_order = case(
        (Tasks.priority == 'HIGH', 1),
        (Tasks.priority == 'MIDDLE', 2),
        (Tasks.priority == 'LOW', 3),
        else_=999  # NULL or any other value
    )

    stmt = stmt.order_by(
        priority_order.asc(),
        Tasks.expires_at.asc(),
    )

    tasks = session.exec(stmt).all()

    print("\nResults:")
    for task in tasks:
        print(f"  {task.title}: priority={task.priority}")
