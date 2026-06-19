"""blacklisted users cannot hold an active registration

Revision ID: d0f2b4c6e8a0
Revises: c9e1a3b5d7f9
Create Date: 2026-06-19 14:15:00.000000

A user blacklisted from an event (event_blacklists) must not hold an active
registration for any of that event's occurrences. The rule spans three tables
(event_registrations -> event_occurrences -> events vs event_blacklists), so it
cannot be a CHECK or EXCLUDE constraint; a BEFORE INSERT OR UPDATE trigger
enforces it. An anulowany row is harmless and stays allowed. See ADR 0006.
"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d0f2b4c6e8a0"
down_revision: Union[str, Sequence[str], None] = "c9e1a3b5d7f9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE OR REPLACE FUNCTION reject_blacklisted_registration()
        RETURNS trigger AS $$
        BEGIN
            IF NEW.status <> 'anulowany' AND EXISTS (
                SELECT 1
                FROM event_occurrences o
                JOIN event_blacklists b ON b.event_id = o.event_id
                WHERE o.id = NEW.occurrence_id AND b.user_id = NEW.user_id
            ) THEN
                RAISE EXCEPTION 'user % is blacklisted from this event', NEW.user_id
                    USING ERRCODE = 'check_violation';
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    op.execute("""
        CREATE TRIGGER trg_event_registrations_reject_blacklisted
        BEFORE INSERT OR UPDATE ON event_registrations
        FOR EACH ROW EXECUTE FUNCTION reject_blacklisted_registration();
    """)


def downgrade() -> None:
    op.execute(
        "DROP TRIGGER trg_event_registrations_reject_blacklisted "
        "ON event_registrations;"
    )
    op.execute("DROP FUNCTION reject_blacklisted_registration();")
