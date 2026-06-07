import uuid

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, status
from psycopg2 import errors

from dependencies import get_db
from schemas import UserCreate, UserRead

router = APIRouter(prefix="/users", tags=["users"])


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
def list_users(db=Depends(get_db)):
    # TODO: paginate
    db.execute("SELECT * FROM users;")
    return db.fetchall()


@router.get("/{user_id}", response_model=UserRead)
def get_user(user_id: uuid.UUID, db=Depends(get_db)):
    db.execute("SELECT * FROM users WHERE id = %s;", (str(user_id),))
    user = db.fetchone()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )
    return user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: uuid.UUID, db=Depends(get_db)):
    db.execute("DELETE FROM users WHERE id = %s RETURNING id;", (str(user_id),))
    deleted = db.fetchone()
    
    if deleted is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )
    return
