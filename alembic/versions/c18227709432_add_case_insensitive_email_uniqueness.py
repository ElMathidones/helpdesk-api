"""add case insensitive email uniqueness

Revision ID: c18227709432
Revises: 389a3ce1dd41
Create Date: 2026-10-17 02:40:24.194456

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c18227709432"
down_revision: Union[str, Sequence[str], None] = "389a3ce1dd41"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "uq_users_email_normalized",
        "users",
        [sa.text("lower(btrim(email))")],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        "uq_users_email_normalized",
        table_name="users",
    )
