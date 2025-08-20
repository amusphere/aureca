"""optimize_chat_performance_indexes

Revision ID: 655e04c7f2b0
Revises: af62fb93b70c
Create Date: 2025-08-17 11:00:57.868258

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "655e04c7f2b0"
down_revision: str | None = "af62fb93b70c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema with performance optimization indexes."""
    # Add missing indexes for optimal chat performance

    # 1. Index on chat_threads.updated_at for thread listing by recency
    op.create_index("idx_chat_threads_updated_at", "chat_threads", ["updated_at"], unique=False)

    # 2. Composite index on (user_id, updated_at) for optimal thread listing
    # This covers the most common query: threads for user ordered by updated_at DESC
    op.create_index(
        "idx_chat_threads_user_updated_desc",
        "chat_threads",
        ["user_id", sa.text("updated_at DESC")],
        unique=False,
    )

    # 3. Composite index for message context retrieval (thread_id, created_at DESC)
    # Optimizes getting recent messages for AI context
    op.create_index(
        "idx_chat_messages_thread_created_desc",
        "chat_messages",
        ["thread_id", sa.text("created_at DESC")],
        unique=False,
    )

    # 4. Partial index for user messages only (for title generation)
    op.create_index(
        "idx_chat_messages_user_role_created",
        "chat_messages",
        ["thread_id", "created_at"],
        unique=False,
        postgresql_where=sa.text("role = 'user'"),
    )


def downgrade() -> None:
    """Downgrade schema by removing performance optimization indexes."""
    # Remove the performance optimization indexes
    op.drop_index("idx_chat_messages_user_role_created", table_name="chat_messages")
    op.drop_index("idx_chat_messages_thread_created_desc", table_name="chat_messages")
    op.drop_index("idx_chat_threads_user_updated_desc", table_name="chat_threads")
    op.drop_index("idx_chat_threads_updated_at", table_name="chat_threads")
