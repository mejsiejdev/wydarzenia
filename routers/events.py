import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from psycopg2 import errors

from dependencies import get_current_user_optional, get_db, require_active_user
from schemas import EventCreate, EventRead, EventStatus

router = APIRouter(prefix="/events", tags=["events"])


def is_event_visible(event, current_user) -> bool:
    # Publiczne i zaakceptowane wydarzenia widzą wszyscy; resztę tylko autor i moderator
    if event["public"] and event["status"] == EventStatus.zaakceptowane.value:
        return True
    if current_user is None:
        return False
    if current_user["status"] == "moderator":
        return True
    return str(event["created_by"]) == str(current_user["id"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=EventRead)
def create_event(
    payload: EventCreate, db=Depends(get_db), current_user=Depends(require_active_user)
):
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
                str(current_user["id"]),
            ),
        )
    except errors.ForeignKeyViolation:
        # Jeśli UUID zalogowanego użytkownika nie istnieje już w tabeli users
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
def list_events(db=Depends(get_db), current_user=Depends(get_current_user_optional)):
    # TODO: paginate (podobnie jak dla users)
    if current_user is not None and current_user["status"] == "moderator":
        db.execute("SELECT * FROM events;")
    elif current_user is not None:
        db.execute(
            """
            SELECT * FROM events
            WHERE (public AND status = 'zaakceptowane') OR created_by = %s;
            """,
            (str(current_user["id"]),),
        )
    else:
        db.execute("SELECT * FROM events WHERE public AND status = 'zaakceptowane';")
    return db.fetchall()


@router.get("/{event_id}", response_model=EventRead)
def get_event(
    event_id: uuid.UUID,
    db=Depends(get_db),
    current_user=Depends(get_current_user_optional),
):
    db.execute("SELECT * FROM events WHERE id = %s;", (str(event_id),))
    event = db.fetchone()
    # Ukryte wydarzenia zwracają 404, aby nie zdradzać ich istnienia
    if event is None or not is_event_visible(event, current_user):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found.",
        )
    return event
