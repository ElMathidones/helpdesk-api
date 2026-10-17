"""add email change password attempt protection

Revision ID: df29743e087a
Revises: c18227709432
Create Date: 2026-10-17 02:53:46.507918

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "df29743e087a"
down_revision: Union[str, Sequence[str], None] = "c18227709432"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "email_change_failed_attempts",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
    )

    op.add_column(
        "users",
        sa.Column(
            "email_change_locked_until",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column(
        "users",
        "email_change_locked_until",
    )

    op.drop_column(
        "users",
        "email_change_failed_attempts",
    )
