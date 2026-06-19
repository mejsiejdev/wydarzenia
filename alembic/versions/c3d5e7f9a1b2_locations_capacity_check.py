"""locations capacity non-negative check

Revision ID: c3d5e7f9a1b2
Revises: b2c4d6e8f0a1
Create Date: 2026-06-19 13:05:00.000000

Parallels ck_events_participant_limit_non_negative (a1f3c9d2e4b7). NULL stays
allowed (unlimited/unknown), otherwise capacity must be non-negative.
"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c3d5e7f9a1b2"
down_revision: Union[str, Sequence[str], None] = "b2c4d6e8f0a1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE locations
        ADD CONSTRAINT ck_locations_capacity_non_negative
        CHECK (capacity >= 0);
    """)


def downgrade() -> None:
    op.execute(
        "ALTER TABLE locations DROP CONSTRAINT ck_locations_capacity_non_negative;"
    )
