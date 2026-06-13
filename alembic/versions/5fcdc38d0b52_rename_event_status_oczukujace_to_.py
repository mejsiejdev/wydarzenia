"""rename event_status oczukujace to oczekujace

Revision ID: 5fcdc38d0b52
Revises: dcd0733ad720
Create Date: 2026-06-13 21:06:51.929993

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '5fcdc38d0b52'
down_revision: Union[str, Sequence[str], None] = 'dcd0733ad720'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "ALTER TYPE event_status RENAME VALUE 'oczukujace_na_akceptacje' TO 'oczekujace_na_akceptacje';"
    )


def downgrade() -> None:
    op.execute(
        "ALTER TYPE event_status RENAME VALUE 'oczekujace_na_akceptacje' TO 'oczukujace_na_akceptacje';"
    )
