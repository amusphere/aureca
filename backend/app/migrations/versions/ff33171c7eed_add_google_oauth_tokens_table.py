"""add_google_oauth_tokens_table

Revision ID: ff33171c7eed
Revises: 55a37c1d5c06
Create Date: 2025-05-24 11:33:33.525975

"""

from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ff33171c7eed"
down_revision: Union[str, None] = "55a37c1d5c06"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "google_oauth_tokens",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("access_token", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("refresh_token", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("token_type", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("expires_at", sa.Float(), nullable=True),
        sa.Column("scope", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("created_at", sa.Float(), nullable=False),
        sa.Column("updated_at", sa.Float(), nullable=False),
        sa.Column("google_user_id", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("google_email", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_google_oauth_tokens_google_user_id"),
        "google_oauth_tokens",
        ["google_user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_google_oauth_tokens_user_id"),
        "google_oauth_tokens",
        ["user_id"],
        unique=False,
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(
        op.f("ix_google_oauth_tokens_user_id"), table_name="google_oauth_tokens"
    )
    op.drop_index(
        op.f("ix_google_oauth_tokens_google_user_id"), table_name="google_oauth_tokens"
    )
    op.drop_table("google_oauth_tokens")
    # ### end Alembic commands ###
