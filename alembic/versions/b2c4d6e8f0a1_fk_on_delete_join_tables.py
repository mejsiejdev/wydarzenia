"""fk on delete policy for event_blacklists and events_categories

Revision ID: b2c4d6e8f0a1
Revises: a1f3c9d2e4b7
Create Date: 2026-06-19 13:00:00.000000

The FKs on event_blacklists (7b0ee76b8025) and events_categories (096084623276)
were created inline with no ON DELETE policy (default NO ACTION). This brings
them in line with ADR 0003: CASCADE for event-child references and for the
banned user, RESTRICT for the moderator/vocabulary references that preserve
history. The inline FKs carry Postgres default names (<table>_<column>_fkey),
so each is dropped by that name and re-added. See ADR 0003.
"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b2c4d6e8f0a1"
down_revision: Union[str, Sequence[str], None] = "a1f3c9d2e4b7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- event_blacklists ---
    op.execute(
        "ALTER TABLE event_blacklists DROP CONSTRAINT event_blacklists_event_id_fkey;"
    )
    op.execute("""
        ALTER TABLE event_blacklists
        ADD CONSTRAINT event_blacklists_event_id_fkey
        FOREIGN KEY (event_id) REFERENCES events (id) ON DELETE CASCADE;
    """)

    op.execute(
        "ALTER TABLE event_blacklists DROP CONSTRAINT event_blacklists_user_id_fkey;"
    )
    op.execute("""
        ALTER TABLE event_blacklists
        ADD CONSTRAINT event_blacklists_user_id_fkey
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE;
    """)

    op.execute(
        "ALTER TABLE event_blacklists DROP CONSTRAINT event_blacklists_blocked_by_fkey;"
    )
    op.execute("""
        ALTER TABLE event_blacklists
        ADD CONSTRAINT event_blacklists_blocked_by_fkey
        FOREIGN KEY (blocked_by) REFERENCES users (id) ON DELETE RESTRICT;
    """)

    # --- events_categories ---
    op.execute(
        "ALTER TABLE events_categories DROP CONSTRAINT events_categories_event_id_fkey;"
    )
    op.execute("""
        ALTER TABLE events_categories
        ADD CONSTRAINT events_categories_event_id_fkey
        FOREIGN KEY (event_id) REFERENCES events (id) ON DELETE CASCADE;
    """)

    op.execute(
        "ALTER TABLE events_categories DROP CONSTRAINT events_categories_category_id_fkey;"
    )
    op.execute("""
        ALTER TABLE events_categories
        ADD CONSTRAINT events_categories_category_id_fkey
        FOREIGN KEY (category_id) REFERENCES event_categories (id) ON DELETE RESTRICT;
    """)


def downgrade() -> None:
    # Restore the plain (NO ACTION) FKs as originally created.
    op.execute(
        "ALTER TABLE events_categories DROP CONSTRAINT events_categories_category_id_fkey;"
    )
    op.execute("""
        ALTER TABLE events_categories
        ADD CONSTRAINT events_categories_category_id_fkey
        FOREIGN KEY (category_id) REFERENCES event_categories (id);
    """)

    op.execute(
        "ALTER TABLE events_categories DROP CONSTRAINT events_categories_event_id_fkey;"
    )
    op.execute("""
        ALTER TABLE events_categories
        ADD CONSTRAINT events_categories_event_id_fkey
        FOREIGN KEY (event_id) REFERENCES events (id);
    """)

    op.execute(
        "ALTER TABLE event_blacklists DROP CONSTRAINT event_blacklists_blocked_by_fkey;"
    )
    op.execute("""
        ALTER TABLE event_blacklists
        ADD CONSTRAINT event_blacklists_blocked_by_fkey
        FOREIGN KEY (blocked_by) REFERENCES users (id);
    """)

    op.execute(
        "ALTER TABLE event_blacklists DROP CONSTRAINT event_blacklists_user_id_fkey;"
    )
    op.execute("""
        ALTER TABLE event_blacklists
        ADD CONSTRAINT event_blacklists_user_id_fkey
        FOREIGN KEY (user_id) REFERENCES users (id);
    """)

    op.execute(
        "ALTER TABLE event_blacklists DROP CONSTRAINT event_blacklists_event_id_fkey;"
    )
    op.execute("""
        ALTER TABLE event_blacklists
        ADD CONSTRAINT event_blacklists_event_id_fkey
        FOREIGN KEY (event_id) REFERENCES events (id);
    """)
