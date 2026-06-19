import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from psycopg2 import errors

from dependencies import (
    get_current_user,
    get_current_user_optional,
    get_db,
    pagination_params,
    require_active_user,
)
from routers.events import is_event_visible, is_owner
from schemas import OccurrenceCreate, OccurrenceRead, OccurrenceStatus, OccurrenceUpdate

router = APIRouter(tags=["occurrences"])


def _load_event(event_id, db):
    db.execute("SELECT * FROM events WHERE id = %s;", (str(event_id),))
    return db.fetchone()


def _load_occurrence_with_event(occurrence_id, db):
    # Zwraca (occurrence, event) albo (None, None), gdy odsłona nie istnieje
    db.execute("SELECT * FROM event_occurrences WHERE id = %s;", (str(occurrence_id),))
    occurrence = db.fetchone()
    if occurrence is None:
        return None, None
    event = _load_event(occurrence["event_id"], db)
    return occurrence, event


def load_visible_occurrence(occurrence_id, db, current_user):
    # Widoczność odsłony dziedziczy z widoczności jej wydarzenia
    occurrence, event = _load_occurrence_with_event(occurrence_id, db)
    if occurrence is None or not is_event_visible(event, current_user):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Occurrence not found.",
        )
    return occurrence, event


def load_writable_occurrence(occurrence_id, db, current_user):
    occurrence, event = load_visible_occurrence(occurrence_id, db, current_user)
    if not is_owner(event, current_user) and current_user["status"] != "moderator":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed to modify this occurrence.",
        )
    return occurrence, event


def check_pwr_availability(location_id, start_time, end_time, db):
    # Sala pwr bez żadnych okien dostępności jest rezerwowalna o każdej porze.
    # Gdy okna istnieją, odsłona musi w całości zmieścić się w jednym z nich.
    db.execute("SELECT type FROM locations WHERE id = %s;", (str(location_id),))
    location = db.fetchone()
    if location is None or location["type"] != "pwr":
        return

    db.execute(
        "SELECT 1 FROM room_availabilities WHERE location_id = %s LIMIT 1;",
        (str(location_id),),
    )
    if db.fetchone() is None:
        return  # brak okien -> dostępna zawsze

    # ISODOW: poniedziałek=1 ... niedziela=7, zgodnie z day_of_week
    db.execute(
        """
        SELECT 1 FROM room_availabilities
        WHERE location_id = %s
          AND (
              (specific_date IS NOT NULL AND specific_date = %s::timestamptz::date)
              OR (day_of_week IS NOT NULL
                  AND day_of_week = EXTRACT(ISODOW FROM %s::timestamptz)::int)
          )
          AND start_time <= %s::timestamptz::time
          AND end_time >= %s::timestamptz::time
        LIMIT 1;
        """,
        (str(location_id), start_time, start_time, start_time, end_time),
    )
    if db.fetchone() is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Occurrence does not fall within the room's availability.",
        )


@router.post(
    "/events/{event_id}/occurrences",
    status_code=status.HTTP_201_CREATED,
    response_model=OccurrenceRead,
)
def create_occurrence(
    event_id: uuid.UUID,
    payload: OccurrenceCreate,
    db=Depends(get_db),
    current_user=Depends(require_active_user),
):
    event = _load_event(event_id, db)
    if event is None or not is_event_visible(event, current_user):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Event not found."
        )
    if not is_owner(event, current_user) and current_user["status"] != "moderator":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed to add occurrences to this event.",
        )
    if payload.end_time <= payload.start_time:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="end_time must be after start_time.",
        )

    check_pwr_availability(
        payload.location_id, payload.start_time, payload.end_time, db
    )

    try:
        db.execute(
            """
            INSERT INTO event_occurrences (event_id, start_time, end_time, location_id, status)
            VALUES (%s, %s, %s, %s, 'zaplanowane')
            RETURNING *;
            """,
            (
                str(event_id),
                payload.start_time,
                payload.end_time,
                str(payload.location_id),
            ),
        )
    except errors.ExclusionViolation:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Location is already booked for an overlapping time.",
        )
    except errors.ForeignKeyViolation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Location specified in 'location_id' does not exist.",
        )

    occurrence = db.fetchone()

    # Twórca odsłony zostaje automatycznie zapisany jako organizator
    db.execute(
        """
        INSERT INTO event_registrations (occurrence_id, user_id, status)
        VALUES (%s, %s, 'organizator');
        """,
        (str(occurrence["id"]), str(current_user["id"])),
    )
    return occurrence


@router.get("/events/{event_id}/occurrences", response_model=list[OccurrenceRead])
def list_occurrences(
    event_id: uuid.UUID,
    db=Depends(get_db),
    current_user=Depends(get_current_user_optional),
    page=Depends(pagination_params),
):
    event = _load_event(event_id, db)
    if event is None or not is_event_visible(event, current_user):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Event not found."
        )
    db.execute(
        """
        SELECT * FROM event_occurrences WHERE event_id = %s
        ORDER BY start_time LIMIT %s OFFSET %s;
        """,
        (str(event_id), page["limit"], page["offset"]),
    )
    return db.fetchall()


@router.get("/occurrences/{occurrence_id}", response_model=OccurrenceRead)
def get_occurrence(
    occurrence_id: uuid.UUID,
    db=Depends(get_db),
    current_user=Depends(get_current_user_optional),
):
    occurrence, _ = load_visible_occurrence(occurrence_id, db, current_user)
    return occurrence


@router.patch("/occurrences/{occurrence_id}", response_model=OccurrenceRead)
def update_occurrence(
    occurrence_id: uuid.UUID,
    payload: OccurrenceUpdate,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    occurrence, _ = load_writable_occurrence(occurrence_id, db, current_user)

    if occurrence["status"] == OccurrenceStatus.odwolane.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A cancelled occurrence cannot be modified.",
        )

    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid fields provided for update.",
        )

    # Wartości docelowe (po nałożeniu zmian) do walidacji czasu i dostępności
    new_start = update_data.get("start_time", occurrence["start_time"])
    new_end = update_data.get("end_time", occurrence["end_time"])
    new_location = update_data.get("location_id", occurrence["location_id"])
    if new_end <= new_start:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="end_time must be after start_time.",
        )

    time_changed = "start_time" in update_data or "end_time" in update_data
    if time_changed or "location_id" in update_data:
        check_pwr_availability(new_location, new_start, new_end, db)

    set_clauses = []
    values = []
    for key, value in update_data.items():
        set_clauses.append(f"{key} = %s")
        values.append(str(value) if key == "location_id" else value)

    # Zmiana terminu zaplanowanej odsłony oznacza ją jako przesuniętą;
    # rejestracje pozostają nienaruszone
    if time_changed and occurrence["status"] == OccurrenceStatus.zaplanowane.value:
        set_clauses.append("status = 'przesuniete'")

    values.append(str(occurrence_id))
    query = (
        f"UPDATE event_occurrences SET {', '.join(set_clauses)} "
        "WHERE id = %s RETURNING *;"
    )
    try:
        db.execute(query, tuple(values))
    except errors.ExclusionViolation:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Location is already booked for an overlapping time.",
        )
    except errors.ForeignKeyViolation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Location specified in 'location_id' does not exist.",
        )
    return db.fetchone()


@router.post("/occurrences/{occurrence_id}/cancel", response_model=OccurrenceRead)
def cancel_occurrence(
    occurrence_id: uuid.UUID,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    occurrence, _ = load_writable_occurrence(occurrence_id, db, current_user)
    if occurrence["status"] not in (
        OccurrenceStatus.zaplanowane.value,
        OccurrenceStatus.przesuniete.value,
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Occurrence is not in a cancellable state.",
        )

    # Odwołanie odsłony anuluje wszystkie jej rejestracje (zachowując historię)
    db.execute(
        "UPDATE event_registrations SET status = 'anulowany' WHERE occurrence_id = %s;",
        (str(occurrence_id),),
    )
    db.execute(
        "UPDATE event_occurrences SET status = 'odwolane' WHERE id = %s RETURNING *;",
        (str(occurrence_id),),
    )
    return db.fetchone()


@router.delete("/occurrences/{occurrence_id}")
def delete_occurrence(
    occurrence_id: uuid.UUID,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    occurrence, _ = load_writable_occurrence(occurrence_id, db, current_user)

    # Tylko organizator (automatyczna rejestracja twórcy) jest dopuszczalny przy
    # twardym usunięciu — jakakolwiek inna rejestracja kieruje do /cancel
    db.execute(
        """
        SELECT 1 FROM event_registrations
        WHERE occurrence_id = %s AND status <> 'organizator' LIMIT 1;
        """,
        (str(occurrence_id),),
    )
    if db.fetchone() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Occurrence has registrations; cancel it instead of deleting.",
        )

    db.execute(
        "DELETE FROM event_registrations WHERE occurrence_id = %s;",
        (str(occurrence_id),),
    )
    db.execute("DELETE FROM event_occurrences WHERE id = %s;", (str(occurrence_id),))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
