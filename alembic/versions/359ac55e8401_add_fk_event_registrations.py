"""add fk event registrations

Revision ID: 359ac55e8401
Revises: dcd0733ad720
Create Date: 2026-06-13 17:07:38.865855

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "359ac55e8401"
down_revision: Union[str, Sequence[str], None] = "5fcdc38d0b52"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Dodanie klucza obcego dla occurrence_id
    op.execute("""
        ALTER TABLE event_registrations
        ADD CONSTRAINT fk_event_registrations_occurrence_id
        FOREIGN KEY (occurrence_id) REFERENCES event_occurrences (id) ON DELETE CASCADE;
    """)
    
    # Dodanie klucza obcego dla user_id
    op.execute("""
        ALTER TABLE event_registrations
        ADD CONSTRAINT fk_event_registrations_user_id
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE;
    """)


def downgrade() -> None:
    # Usunięcie klucza obcego dla user_id
    op.execute("""
        ALTER TABLE event_registrations 
        DROP CONSTRAINT fk_event_registrations_user_id;
    """)
    
    # Usunięcie klucza obcego dla occurrence_id
    op.execute("""
        ALTER TABLE event_registrations 
        DROP CONSTRAINT fk_event_registrations_occurrence_id;
    """)
