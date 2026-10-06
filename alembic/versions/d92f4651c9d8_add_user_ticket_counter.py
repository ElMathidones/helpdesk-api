"""add user ticket counter

Revision ID: d92f4651c9d8
Revises: e2490fc8a7a5
Create Date: 2026-10-06 03:05:13.558046

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d92f4651c9d8"
down_revision: Union[str, Sequence[str], None] = "e2490fc8a7a5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "next_ticket_number",
            sa.Integer(),
            server_default="1",
            nullable=False,
        ),
    )

    op.execute("""
        UPDATE users
        SET next_ticket_number = COALESCE(
            (
                SELECT MAX(tickets.creator_ticket_number) + 1
                FROM tickets
                WHERE tickets.creator_id = users.id
            ),
            1
        )
        """)


def downgrade() -> None:
    op.drop_column(
        "users",
        "next_ticket_number",
    )
