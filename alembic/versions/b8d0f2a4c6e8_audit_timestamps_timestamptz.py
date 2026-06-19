"""remaining naive timestamps to timestamptz

Revision ID: b8d0f2a4c6e8
Revises: a7c9e1b3d5f7
Create Date: 2026-06-19 14:05:00.000000

Converts the remaining naive TIMESTAMP columns to TIMESTAMPTZ:
users.created_at/updated_at, events.created_at, event_access.granted_at,
event_registrations.registered_at, event_blacklists.blocked_at. Existing values
are reinterpreted as Europe/Warsaw wall-clock. The DEFAULT now()/CURRENT_TIMESTAMP
expressions already return timestamptz, so they keep working unchanged.
room_availabilities is unaffected (its time columns are TIME/DATE). See ADR 0005.
"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b8d0f2a4c6e8"
down_revision: Union[str, Sequence[str], None] = "a7c9e1b3d5f7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# (table, column) pairs to convert.
_COLUMNS = [
    ("users", "created_at"),
    ("users", "updated_at"),
    ("events", "created_at"),
    ("event_access", "granted_at"),
    ("event_registrations", "registered_at"),
    ("event_blacklists", "blocked_at"),
]


def upgrade() -> None:
    for table, column in _COLUMNS:
        op.execute(
            f"ALTER TABLE {table} "
            f"ALTER COLUMN {column} TYPE TIMESTAMPTZ "
            f"USING {column} AT TIME ZONE 'Europe/Warsaw';"
        )


def downgrade() -> None:
    for table, column in reversed(_COLUMNS):
        op.execute(
            f"ALTER TABLE {table} "
            f"ALTER COLUMN {column} TYPE TIMESTAMP "
            f"USING {column} AT TIME ZONE 'Europe/Warsaw';"
        )
