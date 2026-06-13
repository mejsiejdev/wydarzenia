"""add fk event registrations

Revision ID: 359ac55e8401
Revises: dcd0733ad720
Create Date: 2026-06-13 17:07:38.865855

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "359ac55e8401"
down_revision: Union[str, Sequence[str], None] = "dcd0733ad720"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Ograniczenie klucza obcego dla occurrence_id
    op.create_foreign_key(
        "fk_event_registrations_occurrence_id",
        "event_registrations",
        "event_occurrences",
        ["occurrence_id"],
        ["id"],
        ondelete="CASCADE",
    )
    # Ograniczenie klucza obcego dla user_id
    op.create_foreign_key(
        "fk_event_registrations_user_id",
        "event_registrations",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_event_registrations_user_id", "event_registrations", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_event_registrations_occurrence_id",
        "event_registrations",
        type_="foreignkey",
    )
