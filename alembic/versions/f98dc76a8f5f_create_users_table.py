"""create_users_table

Revision ID: f98dc76a8f5f
Revises:
Create Date: 2026-04-26 10:10:44.238205

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f98dc76a8f5f"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("""
        CREATE TABLE users (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            email VARCHAR UNIQUE NOT NULL,
            password VARCHAR NOT NULL,
            first_name VARCHAR,
            last_name VARCHAR,
            status UUID,
            blacklisted BOOLEAN NOT NULL DEFAULT false,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP TABLE users;")
