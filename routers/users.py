import uuid

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, status
from psycopg2 import errors

from dependencies import (
    get_current_user,
    get_db,
    pagination_params,
    require_moderator,
)
from schemas import UserCreate, UserRead, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])

# Pola, które na cudzym koncie może zmieniać wyłącznie moderator
MODERATOR_ONLY_FIELDS = {"status", "blacklisted"}


def ensure_self_or_moderator(current_user, user_id: uuid.UUID) -> None:
    if current_user["status"] != "moderator" and str(current_user["id"]) != str(
        user_id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed to access this user.",
        )


@router.post("", status_code=status.HTTP_201_CREATED, response_model=UserRead)
def create_user(payload: UserCreate, db=Depends(get_db)):
    hashed = bcrypt.hashpw(payload.password.encode(), bcrypt.gensalt()).decode()
    try:
        db.execute(
            """
            INSERT INTO users (email, password, first_name, last_name)
            VALUES (%s, %s, %s, %s)
            RETURNING *;
            """,
            (payload.email, hashed, payload.first_name, payload.last_name),
        )
    except errors.UniqueViolation:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists.",
        )
    return db.fetchone()


@router.get("", response_model=list[UserRead])
def list_users(
    db=Depends(get_db),
    _moderator=Depends(require_moderator),
    page=Depends(pagination_params),
):
    db.execute(
        "SELECT * FROM users ORDER BY created_at LIMIT %s OFFSET %s;",
        (page["limit"], page["offset"]),
    )
    return db.fetchall()


@router.get("/{user_id}", response_model=UserRead)
def get_user(
    user_id: uuid.UUID, db=Depends(get_db), current_user=Depends(get_current_user)
):
    ensure_self_or_moderator(current_user, user_id)
    db.execute("SELECT * FROM users WHERE id = %s;", (str(user_id),))
    user = db.fetchone()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: uuid.UUID, db=Depends(get_db), current_user=Depends(get_current_user)
):
    ensure_self_or_moderator(current_user, user_id)
    db.execute("DELETE FROM users WHERE id = %s RETURNING id;", (str(user_id),))
    deleted = db.fetchone()

    if deleted is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )
    return


@router.patch("/{user_id}", response_model=UserRead)
def update_user(
    user_id: uuid.UUID,
    payload: UserUpdate,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    ensure_self_or_moderator(current_user, user_id)

    is_moderator = current_user["status"] == "moderator"
    is_self = str(current_user["id"]) == str(user_id)

    # Odrzucamy wszystkie pola, które nie zostały wprost przesłane przez użytkownika
    update_data = payload.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid fields provided for update.",
        )

    if MODERATOR_ONLY_FIELDS & update_data.keys() and not is_moderator:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only a moderator can change status or blacklist.",
        )

    # Moderator na cudzym koncie może zmieniać wyłącznie status i blacklistę
    if update_data.keys() - MODERATOR_ONLY_FIELDS and not is_self:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the user can change their own profile data.",
        )

    # Należy na nowo zahaszować hasło, jeśli zostało przesłane do zmiany
    if "password" in update_data:
        hashed = bcrypt.hashpw(
            update_data["password"].encode(), bcrypt.gensalt()
        ).decode()
        update_data["password"] = hashed

    # Dynamiczne budowanie zapytania SQL na podstawie przesłanych pól
    set_clauses = []
    values = []

    for key, value in update_data.items():
        set_clauses.append(f"{key} = %s")
        values.append(value)

    set_clauses.append("updated_at = NOW()")
    values.append(str(user_id))

    query = f"UPDATE users SET {', '.join(set_clauses)} WHERE id = %s RETURNING *;"

    try:
        db.execute(query, tuple(values))
    except errors.UniqueViolation:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists.",
        )
    except errors.ForeignKeyViolation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user status.",
        )

    updated_user = db.fetchone()
    if updated_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    return updated_user
