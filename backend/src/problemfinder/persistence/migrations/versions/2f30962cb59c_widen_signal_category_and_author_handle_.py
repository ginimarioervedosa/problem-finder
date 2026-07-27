"""widen signal category and author_handle to text

Committee evidence carries inquiry titles and joint-author handles longer
than the guessed 128-character caps; the domain model imposes no length,
so the columns follow it.

Revision ID: 2f30962cb59c
Revises: 8d54993a4dc2
Create Date: 2026-07-26 17:19:33.210847
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "2f30962cb59c"
down_revision: str | None = "8d54993a4dc2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "signals",
        "category",
        existing_type=sa.VARCHAR(length=128),
        type_=sa.Text(),
        existing_nullable=True,
    )
    op.alter_column(
        "signals",
        "author_handle",
        existing_type=sa.VARCHAR(length=128),
        type_=sa.Text(),
        existing_nullable=True,
    )


def downgrade() -> None:
    # Narrowing back to varchar(128) would truncate or reject stored values.
    raise NotImplementedError("destructive downgrade: stored text exceeds 128 characters")
