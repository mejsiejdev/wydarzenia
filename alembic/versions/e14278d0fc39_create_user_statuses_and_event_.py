"""create_user_statuses_and_event_categories

Revision ID: e14278d0fc39
Revises: f98dc76a8f5f
Create Date: 2026-05-03 15:17:47.671120

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e14278d0fc39'
down_revision: Union[str, Sequence[str], None] = 'f98dc76a8f5f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    op.execute("""
        CREATE TABLE user_statuses (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            status VARCHAR NOT NULL
        );
    """)

    op.execute("""
        CREATE TABLE event_categories (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            category VARCHAR NOT NULL
        );
    """)
    op.execute("""
        CREATE TABLE location_addresses (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            street VARCHAR NOT NULL,
            building_number VARCHAR NOT NULL,
            room_number VARCHAR,
            city VARCHAR NOT NULL,
            postal_code VARCHAR NOT NULL,
            country VARCHAR NOT NULL,
            extra_info TEXT
        );
    """)

def downgrade() -> None:
    op.execute("DROP TABLE location_addresses;")
    op.execute("DROP TABLE event_categories;")
    op.execute("DROP TABLE user_statuses;")
