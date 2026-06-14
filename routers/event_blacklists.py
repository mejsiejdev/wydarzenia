import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from psycopg2 import errors

from dependencies import get_db, require_active_user
from schemas import EventBlacklistCreate, EventBlacklistRead

router = APIRouter(prefix="/event-blacklists", tags=["event_blacklists"])


def check_blacklist_permissions(event_id: uuid.UUID, current_user: dict, db) -> None:
    """Sprawdza czy użytkownik ma prawo edytować listę (moderator lub twórca)."""
    db.execute("SELECT created_by FROM events WHERE id = %s;", (str(event_id),))
    event = db.fetchone()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Event not found."
        )

    if current_user["status"] != "moderator" and str(event["created_by"]) != str(
        current_user["id"]
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to manage blacklists for this event.",
        )


@router.post("", status_code=status.HTTP_201_CREATED, response_model=EventBlacklistRead)
def add_to_blacklist(
    payload: EventBlacklistCreate,
    db=Depends(get_db),
    current_user=Depends(require_active_user),
):
    check_blacklist_permissions(payload.event_id, current_user, db)

    try:
        db.execute(
            """
            INSERT INTO event_blacklists (event_id, user_id, reason)
            VALUES (%s, %s, %s)
            RETURNING *;
            """,
            (str(payload.event_id), str(payload.user_id), payload.reason),
        )
    except errors.UniqueViolation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already blacklisted for this event.",
        )
    except errors.ForeignKeyViolation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid event_id or user_id provided.",
        )

    entry = db.fetchone()
    return entry


@router.get("/{event_id}", response_model=list[EventBlacklistRead])
def list_event_blacklist(
    event_id: uuid.UUID, db=Depends(get_db), current_user=Depends(require_active_user)
):
    check_blacklist_permissions(event_id, current_user, db)

    db.execute("SELECT * FROM event_blacklists WHERE event_id = %s;", (str(event_id),))
    return db.fetchall()
