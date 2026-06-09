from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from config import settings
from dependencies import JWT_ALGORITHM, get_db
from schemas import Token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db=Depends(get_db)):
    # W formularzu OAuth2 pole 'username' przenosi adres e-mail
    db.execute("SELECT * FROM users WHERE email = %s;", (form_data.username,))
    user = db.fetchone()

    if user is None or not bcrypt.checkpw(
        form_data.password.encode(), user["password"].encode()
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user["blacklisted"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is blacklisted.",
        )

    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    access_token = jwt.encode(
        {"sub": str(user["id"]), "exp": expires_at},
        settings.jwt_secret_key,
        algorithm=JWT_ALGORITHM,
    )
    return Token(access_token=access_token)
