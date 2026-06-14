import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from psycopg2 import errors

from dependencies import get_db, require_moderator, get_current_user_optional
from schemas import LocationCreate, LocationRead

router = APIRouter(prefix="/locations", tags=["locations"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=LocationRead)
def create_location(
    payload: LocationCreate, db=Depends(get_db), current_user=Depends(require_moderator)
):
    try:
        db.execute(
            """
            INSERT INTO locations (id, name, address_id, type, capacity, is_active)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING *;
            """,
            (
                str(uuid.uuid4()),
                payload.name,
                str(payload.address_id),
                payload.type.value,
                payload.capacity,
                payload.is_active,
            ),
        )
    except errors.ForeignKeyViolation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Address specified in 'address_id' does not exist.",
        )

    location = db.fetchone()
    if not location:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create location.",
        )
    return location


@router.get("", response_model=list[LocationRead])
def list_locations(db=Depends(get_db), current_user=Depends(get_current_user_optional)):
    # Moderator widzi wszystkie lokacje, zwykły użytkownik tylko aktywne
    if current_user is not None and current_user["status"] == "moderator":
        db.execute("SELECT * FROM locations;")
    else:
        db.execute("SELECT * FROM locations WHERE is_active = true;")
    return db.fetchall()


@router.get("/{location_id}", response_model=LocationRead)
def get_location(
    location_id: uuid.UUID,
    db=Depends(get_db),
    current_user=Depends(get_current_user_optional),
):
    db.execute("SELECT * FROM locations WHERE id = %s;", (str(location_id),))
    location = db.fetchone()

    if location is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Location not found."
        )

    if not location["is_active"] and (
        current_user is None or current_user["status"] != "moderator"
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Location not found."
        )

    return location
