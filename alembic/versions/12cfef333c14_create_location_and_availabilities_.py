"""create_location_and_availabilities_tables

Revision ID: 12cfef333c14
Revises: 7b0ee76b8025
Create Date: 2026-05-25 01:05:51.775424

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '12cfef333c14'
down_revision: Union[str, Sequence[str], None] = '7b0ee76b8025'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE TYPE location_type AS ENUM ('pwr', 'wlasne');")

    # Tabela location_addresses już istnieje z migracji e14278d0fc39.
    # Tutaj tylko dodajemy brakujący DEFAULT 'Polska', który chciałeś wprowadzić.
    op.execute("""
        ALTER TABLE location_addresses 
        ALTER COLUMN country SET DEFAULT 'Polska';
    """)

    op.execute("""
        CREATE TABLE locations (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR NOT NULL,
            address_id UUID NOT NULL REFERENCES location_addresses(id) ON DELETE CASCADE,
            type location_type NOT NULL,
            capacity INT,
            is_active BOOLEAN NOT NULL DEFAULT true
        );
    """)

    op.execute("""
        CREATE TABLE room_availabilities (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            location_id UUID NOT NULL REFERENCES locations(id) ON DELETE CASCADE,
            day_of_week INT NOT NULL CHECK (day_of_week BETWEEN 1 AND 7),
            specific_date DATE,
            start_time TIME NOT NULL,
            end_time TIME NOT NULL
        );
    """)

def downgrade() -> None:
    op.execute("DROP TABLE room_availabilities;")
    op.execute("DROP TABLE locations;")
    
    # Cofnięcie modyfikacji z ALTER TABLE
    op.execute("""
        ALTER TABLE location_addresses 
        ALTER COLUMN country DROP DEFAULT;
    """)
    
    op.execute("DROP TYPE location_type;")
