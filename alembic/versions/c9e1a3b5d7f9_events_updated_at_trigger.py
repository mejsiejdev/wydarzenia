"""events.updated_at column maintained by a BEFORE UPDATE trigger

Revision ID: c9e1a3b5d7f9
Revises: b8d0f2a4c6e8
Create Date: 2026-06-19 14:10:00.000000

events is edited via PATCH and silently reverts to oczekujace_na_akceptacje on a
content edit (ADR 0002), but nothing recorded when that happened. Adds
events.updated_at, kept current by a BEFORE UPDATE trigger so the raw-SQL update
paths cannot forget to bump it.
"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c9e1a3b5d7f9"
down_revision: Union[str, Sequence[str], None] = "b8d0f2a4c6e8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE events ADD COLUMN updated_at TIMESTAMPTZ NOT NULL DEFAULT now();"
    )
    op.execute("""
        CREATE OR REPLACE FUNCTION set_updated_at() RETURNS trigger AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    op.execute("""
        CREATE TRIGGER trg_events_set_updated_at
        BEFORE UPDATE ON events
        FOR EACH ROW EXECUTE FUNCTION set_updated_at();
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER trg_events_set_updated_at ON events;")
    op.execute("DROP FUNCTION set_updated_at();")
    op.execute("ALTER TABLE events DROP COLUMN updated_at;")
