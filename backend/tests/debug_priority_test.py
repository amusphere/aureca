"""Debug test for priority sorting."""

from sqlmodel import Session

from app.repositories.tasks import find_tasks
from app.schema import TaskPriority, Tasks, User


def test_debug_priority_sorting(session: Session, test_user: User):
    """Debug the priority sorting issue."""
    # Create tasks directly in the database
    tasks_data = [
        ("Low Priority Task", TaskPriority.LOW),
        ("High Priority Task", TaskPriority.HIGH),
        ("No Priority Task", None),
        ("Middle Priority Task", TaskPriority.MIDDLE),
    ]

    for i, (title, priority) in enumerate(tasks_data):
        task = Tasks(
            user_id=test_user.id,
            title=title,
            description=f"Description for {title}",
            priority=priority,
            completed=False,
            expires_at=1672617600.0 + i * 86400,  # Different expiry dates
            created_at=1672531200.0,
            updated_at=1672531200.0,
        )
        session.add(task)
    session.commit()

    # Get tasks with priority sorting
    tasks = find_tasks(session=session, user_id=test_user.id, order_by_priority=True)

    # Debug output
    for task in tasks:
        print(f"Title: {task.title}, Priority: {task.priority}, Expires: {task.expires_at}")

    actual_titles = [task.title for task in tasks]
    print(f"Actual order: {actual_titles}")

    # What we expect
    expected_order = [
        "High Priority Task",      # priority = 1
        "Middle Priority Task",    # priority = 2
        "Low Priority Task",       # priority = 3
        "No Priority Task"         # priority = None
    ]
    print(f"Expected order: {expected_order}")

    # Debugging the SQL query
    from sqlalchemy import case
    from sqlmodel import select

    stmt = select(Tasks).where(
        Tasks.user_id == test_user.id,
        not Tasks.completed,
    )

    priority_order = case(
        (Tasks.priority.is_(None), 999),  # Put NULL values at the end
        else_=Tasks.priority
    )
    stmt = stmt.order_by(
        priority_order.asc(),
        Tasks.expires_at.asc(),
    )

    print(f"SQL Query: {stmt}")

    # Let's also check raw data
    all_tasks = session.exec(select(Tasks).where(Tasks.user_id == test_user.id)).all()
    for task in all_tasks:
        priority_val = task.priority.value if task.priority else None
        print(f"Raw: {task.title} -> priority={task.priority} (value={priority_val})")


if __name__ == "__main__":
    # This won't run properly without pytest fixtures
    pass
