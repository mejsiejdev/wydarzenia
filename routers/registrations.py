import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from psycopg2 import errors

from dependencies import get_current_user, get_db, require_active_user
from routers.events import is_owner
from routers.occurrences import load_visible_occurrence
from schemas import RegistrationRead

router = APIRouter(tags=["registrations"])


def _effective_cap(event, location):
    # Pojemność = min(limit wydarzenia, pojemność sali); NULL = brak limitu po danej stronie
    limits = [
        v for v in (event["participant_limit"], location["capacity"]) if v is not None
    ]
    return min(limits) if limits else None


@router.get(
    "/occurrences/{occurrence_id}/registrations",
    response_model=list[RegistrationRead],
)
def list_registrations(
    occurrence_id: uuid.UUID,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    _, event = load_visible_occurrence(occurrence_id, db, current_user)

    if is_owner(event, current_user) or current_user["status"] == "moderator":
        db.execute(
            """
            SELECT * FROM event_registrations WHERE occurrence_id = %s
            ORDER BY registered_at;
            """,
            (str(occurrence_id),),
        )
        return db.fetchall()

    # Zwykły użytkownik widzi wyłącznie własną rejestrację
    db.execute(
        "SELECT * FROM event_registrations WHERE occurrence_id = %s AND user_id = %s;",
        (str(occurrence_id), str(current_user["id"])),
    )
    row = db.fetchone()
    return [row] if row is not None else []


@router.post(
    "/occurrences/{occurrence_id}/registrations",
    status_code=status.HTTP_201_CREATED,
    response_model=RegistrationRead,
)
def sign_up(
    occurrence_id: uuid.UUID,
    db=Depends(get_db),
    current_user=Depends(require_active_user),
):
    occurrence, event = load_visible_occurrence(occurrence_id, db, current_user)

    if occurrence["status"] == "odwolane":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot sign up to a cancelled occurrence.",
        )
    if event["status"] != "zaakceptowane":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Event is not approved.",
        )
    if occurrence["start_time"] <= datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Occurrence has already started.",
        )

    # Blokada wiersza odsłony serializuje równoległe zapisy (wyścig o limit miejsc)
    db.execute(
        "SELECT id FROM event_occurrences WHERE id = %s FOR UPDATE;",
        (str(occurrence_id),),
    )

    db.execute(
        "SELECT status FROM event_registrations WHERE occurrence_id = %s AND user_id = %s;",
        (str(occurrence_id), str(current_user["id"])),
    )
    existing = db.fetchone()
    if existing is not None and existing["status"] != "anulowany":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Already registered for this occurrence.",
        )

    db.execute(
        "SELECT * FROM locations WHERE id = %s;", (str(occurrence["location_id"]),)
    )
    location = db.fetchone()
    cap = _effective_cap(event, location)

    db.execute(
        """
        SELECT count(*) AS n FROM event_registrations
        WHERE occurrence_id = %s AND status = 'zapisany';
        """,
        (str(occurrence_id),),
    )
    taken = db.fetchone()["n"]
    new_status = "zapisany" if cap is None or taken < cap else "rezerwowy"

    try:
        if existing is not None:
            # Ponowny zapis odzyskuje wcześniej anulowany wiersz (PK occurrence_id,user_id)
            db.execute(
                """
                UPDATE event_registrations
                SET status = %s, registered_at = CURRENT_TIMESTAMP
                WHERE occurrence_id = %s AND user_id = %s RETURNING *;
                """,
                (new_status, str(occurrence_id), str(current_user["id"])),
            )
        else:
            db.execute(
                """
                INSERT INTO event_registrations (occurrence_id, user_id, status)
                VALUES (%s, %s, %s) RETURNING *;
                """,
                (str(occurrence_id), str(current_user["id"]), new_status),
            )
    except errors.CheckViolation:
        # Trigger reject_blacklisted_registration (ADR 0006)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are blacklisted from this event.",
        )
    return db.fetchone()


@router.delete(
    "/occurrences/{occurrence_id}/registrations/me",
    response_model=RegistrationRead,
)
def cancel_registration(
    occurrence_id: uuid.UUID,
    db=Depends(get_db),
    current_user=Depends(require_active_user),
):
    # Blokada odsłony serializuje anulowanie z ewentualną promocją z listy rezerwowej
    db.execute(
        "SELECT id FROM event_occurrences WHERE id = %s FOR UPDATE;",
        (str(occurrence_id),),
    )
    if db.fetchone() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Occurrence not found."
        )

    db.execute(
        "SELECT * FROM event_registrations WHERE occurrence_id = %s AND user_id = %s;",
        (str(occurrence_id), str(current_user["id"])),
    )
    registration = db.fetchone()
    if registration is None or registration["status"] == "anulowany":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Registration not found."
        )

    was_zapisany = registration["status"] == "zapisany"

    db.execute(
        """
        UPDATE event_registrations SET status = 'anulowany'
        WHERE occurrence_id = %s AND user_id = %s RETURNING *;
        """,
        (str(occurrence_id), str(current_user["id"])),
    )
    cancelled = db.fetchone()

    # Zwolnienie liczonego miejsca promuje najstarszego rezerwowego (FIFO)
    if was_zapisany:
        db.execute(
            """
            UPDATE event_registrations SET status = 'zapisany'
            WHERE (occurrence_id, user_id) = (
                SELECT occurrence_id, user_id FROM event_registrations
                WHERE occurrence_id = %s AND status = 'rezerwowy'
                ORDER BY registered_at LIMIT 1
            );
            """,
            (str(occurrence_id),),
        )

    return cancelled
