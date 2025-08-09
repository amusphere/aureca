"""migrate_ai_chat_usage_logs_to_ai_chat_usage

Revision ID: f1a2b3c4d5e6
Revises: e89ba24a8c2b
Create Date: 2025-08-07 12:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f1a2b3c4d5e6"
down_revision: str | None = "e89ba24a8c2b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Rename table from ai_chat_usage_logs to ai_chat_usage
    op.rename_table("ai_chat_usage_logs", "ai_chat_usage")

    # Drop old indexes
    op.drop_index("ix_ai_chat_usage_logs_user_id", table_name="ai_chat_usage")
    op.drop_index("ix_ai_chat_usage_logs_usage_date", table_name="ai_chat_usage")

    # Create new optimized indexes with new table name
    op.create_index("ix_ai_chat_usage_user_id", "ai_chat_usage", ["user_id"], unique=False)
    op.create_index("ix_ai_chat_usage_usage_date", "ai_chat_usage", ["usage_date"], unique=False)

    # Create optimized composite index for fast lookups
    op.create_index("idx_user_date_fast", "ai_chat_usage", ["user_id", "usage_date"], unique=False)

    # Update the unique constraint name to match new table
    op.drop_constraint("uq_user_usage_date", "ai_chat_usage", type_="unique")
    op.create_unique_constraint("uq_ai_chat_usage_user_date", "ai_chat_usage", ["user_id", "usage_date"])


def downgrade() -> None:
    """Downgrade schema."""
    # Drop new indexes and constraints
    op.drop_index("idx_user_date_fast", table_name="ai_chat_usage")
    op.drop_constraint("uq_ai_chat_usage_user_date", "ai_chat_usage", type_="unique")
    op.drop_index("ix_ai_chat_usage_usage_date", table_name="ai_chat_usage")
    op.drop_index("ix_ai_chat_usage_user_id", table_name="ai_chat_usage")

    # Rename table back to original name
    op.rename_table("ai_chat_usage", "ai_chat_usage_logs")

    # Recreate original indexes
    op.create_index("ix_ai_chat_usage_logs_user_id", "ai_chat_usage_logs", ["user_id"], unique=False)
    op.create_index("ix_ai_chat_usage_logs_usage_date", "ai_chat_usage_logs", ["usage_date"], unique=False)

    # Recreate original unique constraint
    op.create_unique_constraint("uq_user_usage_date", "ai_chat_usage_logs", ["user_id", "usage_date"])
