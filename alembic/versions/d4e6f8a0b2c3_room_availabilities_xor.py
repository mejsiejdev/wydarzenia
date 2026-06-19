"""room_availabilities recurring-vs-specific xor

Revision ID: d4e6f8a0b2c3
Revises: c3d5e7f9a1b2
Create Date: 2026-06-19 13:10:00.000000

Each window is either a recurring weekly window (day_of_week) or a one-off
specific-date window (specific_date), never both and never neither. day_of_week
becomes nullable so a pure one-off row is possible; a CHECK enforces the XOR.
The existing day_of_week BETWEEN 1 AND 7 check is unaffected (passes on NULL).
Table is dormant (no router consumers), so no data backfill is needed.
"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d4e6f8a0b2c3"
down_revision: Union[str, Sequence[str], None] = "c3d5e7f9a1b2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE room_availabilities ALTER COLUMN day_of_week DROP NOT NULL;"
    )
    op.execute("""
        ALTER TABLE room_availabilities
        ADD CONSTRAINT ck_room_availabilities_recurring_xor_specific
        CHECK ((day_of_week IS NOT NULL) <> (specific_date IS NOT NULL));
    """)


def downgrade() -> None:
    op.execute(
        "ALTER TABLE room_availabilities "
        "DROP CONSTRAINT ck_room_availabilities_recurring_xor_specific;"
    )
    op.execute("ALTER TABLE room_availabilities ALTER COLUMN day_of_week SET NOT NULL;")
