"""no location double-booking on event_occurrences

Revision ID: e5f7a9b1c3d4
Revises: d4e6f8a0b2c3
Create Date: 2026-06-19 13:15:00.000000

Guarantees at the DB level that no two active occurrences share a location and
an overlapping time range. Uses a GiST exclusion constraint (needs btree_gist
for the equality part on location_id). Cancelled occurrences (odwolane) do not
reserve the room and are excluded from the constraint. See ADR 0004.
"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e5f7a9b1c3d4"
down_revision: Union[str, Sequence[str], None] = "d4e6f8a0b2c3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist;")
    op.execute("""
        ALTER TABLE event_occurrences
        ADD CONSTRAINT ex_event_occurrences_no_location_overlap
        EXCLUDE USING gist (
            location_id WITH =,
            tsrange(start_time, end_time) WITH &&
        ) WHERE (status <> 'odwolane');
    """)


def downgrade() -> None:
    op.execute(
        "ALTER TABLE event_occurrences "
        "DROP CONSTRAINT ex_event_occurrences_no_location_overlap;"
    )
    # btree_gist is left installed: harmless and potentially shared.
