"""add email change verification fields

Revision ID: 389a3ce1dd41
Revises: d92f4651c9d8
Create Date: 2026-10-16 23:42:53.063512

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "389a3ce1dd41"
down_revision: Union[str, Sequence[str], None] = "d92f4651c9d8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "pending_email",
            sa.String(length=255),
            nullable=True,
        ),
    )

    op.add_column(
        "users",
        sa.Column(
            "email_change_token_hash",
            sa.String(length=64),
            nullable=True,
        ),
    )

    op.add_column(
        "users",
        sa.Column(
            "email_change_expires_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.add_column(
        "users",
        sa.Column(
            "email_change_requested_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "email_change_requested_at")
    op.drop_column("users", "email_change_expires_at")
    op.drop_column("users", "email_change_token_hash")
    op.drop_column("users", "pending_email")
