import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from psycopg2 import errors

from dependencies import (
    get_current_user,
    get_current_user_optional,
    get_db,
    pagination_params,
    require_active_user,
    require_moderator,
)
from schemas import EventCreate, EventRead, EventStatus, EventUpdate

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


def is_owner(event, user) -> bool:
    return str(event["created_by"]) == str(user["id"])


def load_visible_event(event_id, db, current_user):
    db.execute("SELECT * FROM events WHERE id = %s;", (str(event_id),))
    event = db.fetchone()
    if event is None or not is_event_visible(event, current_user):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found.",
        )
    return event


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
            VALUES (%s, %s, %s, 'szkic', %s, %s, %s)
            RETURNING *;
            """,
            (
                payload.title,
                payload.description,
                payload.public,
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
def list_events(
    db=Depends(get_db),
    current_user=Depends(get_current_user_optional),
    page=Depends(pagination_params),
):
    if current_user is not None and current_user["status"] == "moderator":
        db.execute(
            "SELECT * FROM events ORDER BY created_at LIMIT %s OFFSET %s;",
            (page["limit"], page["offset"]),
        )
    elif current_user is not None:
        db.execute(
            """
            SELECT * FROM events
            WHERE (public AND status = 'zaakceptowane') OR created_by = %s
            ORDER BY created_at LIMIT %s OFFSET %s;
            """,
            (str(current_user["id"]), page["limit"], page["offset"]),
        )
    else:
        db.execute(
            """
            SELECT * FROM events
            WHERE public AND status = 'zaakceptowane'
            ORDER BY created_at LIMIT %s OFFSET %s;
            """,
            (page["limit"], page["offset"]),
        )
    return db.fetchall()


@router.get("/{event_id}", response_model=EventRead)
def get_event(
    event_id: uuid.UUID,
    db=Depends(get_db),
    current_user=Depends(get_current_user_optional),
):
    # Ukryte wydarzenia zwracają 404, aby nie zdradzać ich istnienia
    return load_visible_event(event_id, db, current_user)


@router.patch("/{event_id}", response_model=EventRead)
def update_event(
    event_id: uuid.UUID,
    payload: EventUpdate,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    event = load_visible_event(event_id, db, current_user)

    is_moderator = current_user["status"] == "moderator"
    if not is_owner(event, current_user) and not is_moderator:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed to modify this event.",
        )

    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid fields provided for update.",
        )

    # Dynamiczne budowanie zapytania SQL na podstawie przesłanych pól
    set_clauses = []
    values = []
    for key, value in update_data.items():
        set_clauses.append(f"{key} = %s")
        values.append(value)

    # Edycja treści zaakceptowanego/odrzuconego wydarzenia cofa je do ponownej recenzji
    if event["status"] in (
        EventStatus.zaakceptowane.value,
        EventStatus.odrzucone.value,
    ):
        set_clauses.append("status = 'oczekujace_na_akceptacje'")

    values.append(str(event_id))
    query = f"UPDATE events SET {', '.join(set_clauses)} WHERE id = %s RETURNING *;"

    db.execute(query, tuple(values))
    return db.fetchone()


def _transition(event_id, db, current_user, *, expected, new_status):
    event = load_visible_event(event_id, db, current_user)
    if event["status"] != expected:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Event is not in '{expected}'.",
        )
    db.execute(
        "UPDATE events SET status = %s WHERE id = %s RETURNING *;",
        (new_status, str(event_id)),
    )
    return db.fetchone()


@router.post("/{event_id}/submit", response_model=EventRead)
def submit_event(
    event_id: uuid.UUID,
    db=Depends(get_db),
    current_user=Depends(require_active_user),
):
    # Tylko autor może zgłosić swój szkic do akceptacji
    event = load_visible_event(event_id, db, current_user)
    if not is_owner(event, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the owner can submit this event.",
        )
    return _transition(
        event_id,
        db,
        current_user,
        expected=EventStatus.szkic.value,
        new_status=EventStatus.oczekujace_na_akceptacje.value,
    )


@router.post("/{event_id}/approve", response_model=EventRead)
def approve_event(
    event_id: uuid.UUID,
    db=Depends(get_db),
    current_user=Depends(require_moderator),
):
    return _transition(
        event_id,
        db,
        current_user,
        expected=EventStatus.oczekujace_na_akceptacje.value,
        new_status=EventStatus.zaakceptowane.value,
    )


@router.post("/{event_id}/reject", response_model=EventRead)
def reject_event(
    event_id: uuid.UUID,
    db=Depends(get_db),
    current_user=Depends(require_moderator),
):
    return _transition(
        event_id,
        db,
        current_user,
        expected=EventStatus.oczekujace_na_akceptacje.value,
        new_status=EventStatus.odrzucone.value,
    )


@router.delete("/{event_id}", response_model=EventRead)
def delete_event(
    event_id: uuid.UUID,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    event = load_visible_event(event_id, db, current_user)

    is_moderator = current_user["status"] == "moderator"
    if not is_owner(event, current_user) and not is_moderator:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed to delete this event.",
        )

    # Czy istnieje jakakolwiek rejestracja na którąkolwiek odsłonę wydarzenia?
    db.execute(
        """
        SELECT 1 FROM event_registrations r
        JOIN event_occurrences o ON o.id = r.occurrence_id
        WHERE o.event_id = %s LIMIT 1;
        """,
        (str(event_id),),
    )
    has_registrations = db.fetchone() is not None

    if has_registrations:
        # Ustawienie wydarzenia jako odwolane
        db.execute(
            """
            UPDATE event_registrations SET status = 'anulowany'
            WHERE occurrence_id IN (
                SELECT id FROM event_occurrences WHERE event_id = %s
            );
            """,
            (str(event_id),),
        )
        db.execute(
            "UPDATE event_occurrences SET status = 'odwolane' WHERE event_id = %s;",
            (str(event_id),),
        )
        db.execute("SELECT * FROM events WHERE id = %s;", (str(event_id),))
        return db.fetchone()

    # Pełne usunięcie wydarzenia
    db.execute("DELETE FROM events_categories WHERE event_id = %s;", (str(event_id),))
    db.execute("DELETE FROM event_blacklists WHERE event_id = %s;", (str(event_id),))
    db.execute("DELETE FROM event_access WHERE event_id = %s;", (str(event_id),))
    db.execute("DELETE FROM event_occurrences WHERE event_id = %s;", (str(event_id),))
    db.execute("DELETE FROM events WHERE id = %s;", (str(event_id),))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
