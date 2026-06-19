"""users created_at/updated_at not null

Revision ID: f6a8b0c2d4e5
Revises: e5f7a9b1c3d4
Create Date: 2026-06-19 13:20:00.000000

The original users table (f98dc76a8f5f) left created_at/updated_at nullable
despite their DEFAULT NOW(). Backfill any NULLs and make them NOT NULL to match
the rest of the schema's timestamp columns.
"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f6a8b0c2d4e5"
down_revision: Union[str, Sequence[str], None] = "e5f7a9b1c3d4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("UPDATE users SET created_at = NOW() WHERE created_at IS NULL;")
    op.execute("UPDATE users SET updated_at = NOW() WHERE updated_at IS NULL;")
    op.execute("ALTER TABLE users ALTER COLUMN created_at SET NOT NULL;")
    op.execute("ALTER TABLE users ALTER COLUMN updated_at SET NOT NULL;")


def downgrade() -> None:
    op.execute("ALTER TABLE users ALTER COLUMN updated_at DROP NOT NULL;")
    op.execute("ALTER TABLE users ALTER COLUMN created_at DROP NOT NULL;")
