"""create_event_blacklists

Revision ID: 7b0ee76b8025
Revises: 54946b80e36b
Create Date: 2026-05-21 18:04:58.849341

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7b0ee76b8025"
down_revision: Union[str, Sequence[str], None] = "096084623276"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("""
        CREATE TABLE event_blacklists (
            event_id UUID NOT NULL REFERENCES events(id),
            user_id UUID NOT NULL REFERENCES users(id),
            reason TEXT NOT NULL,
            blocked_by UUID NOT NULL REFERENCES users(id),
            blocked_at TIMESTAMP NOT NULL DEFAULT NOW(),
            PRIMARY KEY (event_id, user_id)
    );""")
    pass


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP TABLE event_blacklists;")
    pass
