"""user_statuses_dict_table

Revision ID: c22b51584b57
Revises: 12cfef333c14
Create Date: 2026-05-30 19:38:18.526806

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c22b51584b57"
down_revision: Union[str, Sequence[str], None] = "12cfef333c14"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TABLE user_statuses DROP CONSTRAINT user_statuses_status_key;")
    op.execute("ALTER TABLE user_statuses DROP CONSTRAINT user_statuses_pkey;")
    op.execute("ALTER TABLE user_statuses DROP COLUMN id;")
    op.execute("ALTER TABLE user_statuses ADD PRIMARY KEY (status);")

    op.execute("""
        INSERT INTO user_statuses (status)
        VALUES ('nieaktywowany'), ('zwykły'), ('zaufany'), ('moderator');
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("""
        DELETE FROM user_statuses
        WHERE status IN ('nieaktywowany', 'zwykły', 'zaufany', 'moderator');
    """)
    op.execute("ALTER TABLE user_statuses DROP CONSTRAINT user_statuses_pkey;")
    op.execute(
        "ALTER TABLE user_statuses ADD COLUMN id UUID PRIMARY KEY DEFAULT gen_random_uuid();"
    )
    op.execute(
        "ALTER TABLE user_statuses ADD CONSTRAINT user_statuses_status_key UNIQUE (status);"
    )
