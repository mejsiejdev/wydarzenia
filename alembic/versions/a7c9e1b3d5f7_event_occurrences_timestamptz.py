"""event_occurrences start_time/end_time to timestamptz

Revision ID: a7c9e1b3d5f7
Revises: f6a8b0c2d4e5
Create Date: 2026-06-19 14:00:00.000000

Converts event_occurrences.start_time/end_time from naive TIMESTAMP to
TIMESTAMPTZ. The GiST no-double-booking exclusion constraint
(ex_event_occurrences_no_location_overlap, ADR 0004) references
tsrange(start_time, end_time), so it is dropped before the column type changes
and recreated against tstzrange. Existing naive values are reinterpreted as
Europe/Warsaw wall-clock. See ADR 0005.
"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a7c9e1b3d5f7"
down_revision: Union[str, Sequence[str], None] = "f6a8b0c2d4e5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE event_occurrences "
        "DROP CONSTRAINT ex_event_occurrences_no_location_overlap;"
    )
    op.execute("""
        ALTER TABLE event_occurrences
        ALTER COLUMN start_time TYPE TIMESTAMPTZ
        USING start_time AT TIME ZONE 'Europe/Warsaw';
    """)
    op.execute("""
        ALTER TABLE event_occurrences
        ALTER COLUMN end_time TYPE TIMESTAMPTZ
        USING end_time AT TIME ZONE 'Europe/Warsaw';
    """)
    op.execute("""
        ALTER TABLE event_occurrences
        ADD CONSTRAINT ex_event_occurrences_no_location_overlap
        EXCLUDE USING gist (
            location_id WITH =,
            tstzrange(start_time, end_time) WITH &&
        ) WHERE (status <> 'odwolane');
    """)


def downgrade() -> None:
    op.execute(
        "ALTER TABLE event_occurrences "
        "DROP CONSTRAINT ex_event_occurrences_no_location_overlap;"
    )
    op.execute("""
        ALTER TABLE event_occurrences
        ALTER COLUMN end_time TYPE TIMESTAMP
        USING end_time AT TIME ZONE 'Europe/Warsaw';
    """)
    op.execute("""
        ALTER TABLE event_occurrences
        ALTER COLUMN start_time TYPE TIMESTAMP
        USING start_time AT TIME ZONE 'Europe/Warsaw';
    """)
    op.execute("""
        ALTER TABLE event_occurrences
        ADD CONSTRAINT ex_event_occurrences_no_location_overlap
        EXCLUDE USING gist (
            location_id WITH =,
            tsrange(start_time, end_time) WITH &&
        ) WHERE (status <> 'odwolane');
    """)
