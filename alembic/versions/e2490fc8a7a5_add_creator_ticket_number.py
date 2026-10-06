"""add creator ticket number

Revision ID: e2490fc8a7a5
Revises: d7bac1b053da
Create Date: 2026-10-06 02:35:46.606465

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e2490fc8a7a5"
down_revision: Union[str, Sequence[str], None] = "d7bac1b053da"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "tickets",
        sa.Column(
            "creator_ticket_number",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.execute("""
        WITH numbered_tickets AS (
            SELECT
                id,
                ROW_NUMBER() OVER (
                    PARTITION BY creator_id
                    ORDER BY created_at, id
                ) AS creator_ticket_number
            FROM tickets
        )
        UPDATE tickets
        SET creator_ticket_number =
            numbered_tickets.creator_ticket_number
        FROM numbered_tickets
        WHERE tickets.id = numbered_tickets.id
        """)

    op.alter_column(
        "tickets",
        "creator_ticket_number",
        existing_type=sa.Integer(),
        nullable=False,
    )

    op.create_unique_constraint(
        "uq_tickets_creator_ticket_number",
        "tickets",
        ["creator_id", "creator_ticket_number"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_tickets_creator_ticket_number",
        "tickets",
        type_="unique",
    )

    op.drop_column(
        "tickets",
        "creator_ticket_number",
    )
