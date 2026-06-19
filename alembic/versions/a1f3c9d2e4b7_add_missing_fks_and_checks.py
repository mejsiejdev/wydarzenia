"""add missing foreign keys and check constraints

Revision ID: a1f3c9d2e4b7
Revises: 359ac55e8401
Create Date: 2026-06-19 12:00:00.000000

Adds the foreign keys that the tables created in 54946b80e36b never received
(only event_registrations was retrofitted, in 359ac55e8401), plus a few CHECK
constraints. ON DELETE policy: CASCADE for event-child references to events(id),
RESTRICT for references to users(id) and locations(id). See ADR 0003.
"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1f3c9d2e4b7"
down_revision: Union[str, Sequence[str], None] = "359ac55e8401"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- events.created_by -> users(id) : RESTRICT ---
    op.execute("""
        ALTER TABLE events
        ADD CONSTRAINT fk_events_created_by
        FOREIGN KEY (created_by) REFERENCES users (id) ON DELETE RESTRICT;
    """)

    # --- event_access -> events(id) CASCADE, users(id) CASCADE/RESTRICT ---
    op.execute("""
        ALTER TABLE event_access
        ADD CONSTRAINT fk_event_access_event_id
        FOREIGN KEY (event_id) REFERENCES events (id) ON DELETE CASCADE;
    """)
    op.execute("""
        ALTER TABLE event_access
        ADD CONSTRAINT fk_event_access_user_id
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE;
    """)
    op.execute("""
        ALTER TABLE event_access
        ADD CONSTRAINT fk_event_access_granted_by
        FOREIGN KEY (granted_by) REFERENCES users (id) ON DELETE RESTRICT;
    """)

    # --- event_occurrences -> events(id) CASCADE, locations(id) RESTRICT ---
    op.execute("""
        ALTER TABLE event_occurrences
        ADD CONSTRAINT fk_event_occurrences_event_id
        FOREIGN KEY (event_id) REFERENCES events (id) ON DELETE CASCADE;
    """)
    op.execute("""
        ALTER TABLE event_occurrences
        ADD CONSTRAINT fk_event_occurrences_location_id
        FOREIGN KEY (location_id) REFERENCES locations (id) ON DELETE RESTRICT;
    """)

    # --- CHECK constraints ---
    op.execute("""
        ALTER TABLE event_occurrences
        ADD CONSTRAINT ck_event_occurrences_time_order
        CHECK (end_time > start_time);
    """)
    op.execute("""
        ALTER TABLE room_availabilities
        ADD CONSTRAINT ck_room_availabilities_time_order
        CHECK (end_time > start_time);
    """)
    op.execute("""
        ALTER TABLE events
        ADD CONSTRAINT ck_events_participant_limit_non_negative
        CHECK (participant_limit >= 0);
    """)


def downgrade() -> None:
    op.execute(
        "ALTER TABLE events DROP CONSTRAINT ck_events_participant_limit_non_negative;"
    )
    op.execute(
        "ALTER TABLE room_availabilities DROP CONSTRAINT ck_room_availabilities_time_order;"
    )
    op.execute(
        "ALTER TABLE event_occurrences DROP CONSTRAINT ck_event_occurrences_time_order;"
    )

    op.execute(
        "ALTER TABLE event_occurrences DROP CONSTRAINT fk_event_occurrences_location_id;"
    )
    op.execute(
        "ALTER TABLE event_occurrences DROP CONSTRAINT fk_event_occurrences_event_id;"
    )

    op.execute("ALTER TABLE event_access DROP CONSTRAINT fk_event_access_granted_by;")
    op.execute("ALTER TABLE event_access DROP CONSTRAINT fk_event_access_user_id;")
    op.execute("ALTER TABLE event_access DROP CONSTRAINT fk_event_access_event_id;")

    op.execute("ALTER TABLE events DROP CONSTRAINT fk_events_created_by;")
