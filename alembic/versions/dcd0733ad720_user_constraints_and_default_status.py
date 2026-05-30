"""user_constraints_and_default_status

Revision ID: dcd0733ad720
Revises: c22b51584b57
Create Date: 2026-05-30 19:38:19.672397

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "dcd0733ad720"
down_revision: Union[str, Sequence[str], None] = "c22b51584b57"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TABLE users ALTER COLUMN status TYPE VARCHAR USING status::text;")
    op.execute("UPDATE users SET status = 'nieaktywowany' WHERE status IS NULL;")
    op.execute("ALTER TABLE users ALTER COLUMN status SET DEFAULT 'nieaktywowany';")
    op.execute("ALTER TABLE users ALTER COLUMN status SET NOT NULL;")
    op.execute("""
        ALTER TABLE users ADD CONSTRAINT users_status_fkey
        FOREIGN KEY (status) REFERENCES user_statuses(status) ON UPDATE CASCADE;
    """)

    op.execute("ALTER TABLE users ALTER COLUMN first_name SET NOT NULL;")
    op.execute("ALTER TABLE users ALTER COLUMN last_name SET NOT NULL;")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("ALTER TABLE users ALTER COLUMN last_name DROP NOT NULL;")
    op.execute("ALTER TABLE users ALTER COLUMN first_name DROP NOT NULL;")

    op.execute("ALTER TABLE users DROP CONSTRAINT users_status_fkey;")
    op.execute("ALTER TABLE users ALTER COLUMN status DROP NOT NULL;")
    op.execute("ALTER TABLE users ALTER COLUMN status DROP DEFAULT;")
    op.execute("ALTER TABLE users ALTER COLUMN status TYPE UUID USING status::uuid;")
