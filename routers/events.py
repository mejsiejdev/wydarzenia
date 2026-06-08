import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from psycopg2 import errors

from dependencies import get_db
from schemas import EventCreate, EventRead

router = APIRouter(prefix="/events", tags=["events"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=EventRead)
def create_event(payload: EventCreate, db=Depends(get_db)):
    try:
        db.execute(
            """
            INSERT INTO events (
                title, description, public, status, 
                participant_limit, social_media_links, created_by
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING *;
            """,
            (
                payload.title,
                payload.description,
                payload.public,
                payload.status.value,
                payload.participant_limit,
                payload.social_media_links,
                str(payload.created_by),
            ),
        )
    except errors.ForeignKeyViolation:
        # Jeśli podany UUID 'created_by' nie istnieje w tabeli users
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User specified in 'created_by' does not exist.",
        )

    event = db.fetchone()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create event.",
        )
    return event


@router.get("", response_model=list[EventRead])
def list_events(db=Depends(get_db)):
    # TODO: paginate (podobnie jak dla users)
    db.execute("SELECT * FROM events;")
    return db.fetchall()


@router.get("/{event_id}", response_model=EventRead)
def get_event(event_id: uuid.UUID, db=Depends(get_db)):
    db.execute("SELECT * FROM events WHERE id = %s;", (str(event_id),))
    event = db.fetchone()
    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found.",
        )
    return event
