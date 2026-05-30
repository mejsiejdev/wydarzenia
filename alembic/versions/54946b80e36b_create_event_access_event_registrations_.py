"""create_event_access_event_registrations_event_occurrences_events_tables

Revision ID: 54946b80e36b
Revises: e14278d0fc39
Create Date: 2026-05-11 16:27:06.325730

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "54946b80e36b"
down_revision: Union[str, Sequence[str], None] = "e14278d0fc39"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "CREATE TYPE event_status AS ENUM ('szkic', 'oczukujace_na_akceptacje', 'zaakceptowane', 'odrzucone');"
    )
    op.execute(
        "CREATE TYPE occurrence_status AS ENUM ('zaplanowane', 'odwolane', 'przesuniete');"
    )
    op.execute(
        "CREATE TYPE registration_status AS ENUM ('organizator', 'zapisany', 'rezerwowy', 'anulowany');"
    )

    op.execute("""
        CREATE TABLE events (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            title VARCHAR NOT NULL,
            description TEXT,
            public BOOLEAN NOT NULL,
            status event_status NOT NULL,
            participant_limit INT,
            social_media_links TEXT,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            created_by UUID NOT NULL
        );
    """)

    op.execute("""
        CREATE TABLE event_access (
            event_id UUID NOT NULL,
            user_id UUID NOT NULL,
            granted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            granted_by UUID NOT NULL,
            PRIMARY KEY (event_id, user_id)
        );
    """)

    op.execute("""
        CREATE TABLE event_occurrences (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            event_id UUID NOT NULL,
            start_time TIMESTAMP NOT NULL,
            end_time TIMESTAMP NOT NULL,
            location_id UUID NOT NULL,
            status occurrence_status NOT NULL
        );
    """)

    op.execute("""
        CREATE TABLE event_registrations (
            occurrence_id UUID NOT NULL,
            user_id UUID NOT NULL,
            status registration_status NOT NULL,
            registered_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (occurrence_id, user_id)
        );
    """)


def downgrade() -> None:
    op.execute("DROP TABLE event_registrations;")
    op.execute("DROP TABLE event_occurrences;")
    op.execute("DROP TABLE event_access;")
    op.execute("DROP TABLE events;")
    op.execute("DROP TYPE registration_status;")
    op.execute("DROP TYPE occurrence_status;")
    op.execute("DROP TYPE event_status;")
