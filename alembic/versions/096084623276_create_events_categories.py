"""create_events_categories

Revision ID: 096084623276
Revises: 54946b80e36b
Create Date: 2026-05-21 18:00:30.180681

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "096084623276"
down_revision: Union[str, Sequence[str], None] = "54946b80e36b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("""
        CREATE TABLE events_categories (
            event_id UUID NOT NULL REFERENCES events(id),
            category_id UUID NOT NULL REFERENCES event_categories(id),
            PRIMARY KEY (event_id, category_id)
        )
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP TABLE events_categories")
    pass
