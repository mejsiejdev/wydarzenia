from collections.abc import Generator

import jwt
from fastapi import Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer
from psycopg2 import pool
from psycopg2.extras import RealDictCursor

from config import settings

JWT_ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)

connection_pool = pool.ThreadedConnectionPool(
    minconn=1,
    maxconn=10,
    dsn=settings.database_url,
)


def get_db() -> Generator:
    conn = connection_pool.getconn()
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        yield cursor
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        connection_pool.putconn(conn)


def get_current_user(token: str = Depends(oauth2_scheme), db=Depends(get_db)):
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[JWT_ALGORITHM])
    except jwt.InvalidTokenError:
        raise credentials_error

    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_error

    db.execute("SELECT * FROM users WHERE id = %s;", (user_id,))
    user = db.fetchone()
    if user is None:
        raise credentials_error

    if user["blacklisted"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is blacklisted.",
        )
    return user


def get_current_user_optional(
    token: str | None = Depends(oauth2_scheme_optional), db=Depends(get_db)
):
    # Anonimowy dostęp jest dozwolony — nieprawidłowy token traktujemy jak jego brak
    if token is None:
        return None
    try:
        return get_current_user(token, db)
    except HTTPException:
        return None


def require_moderator(user=Depends(get_current_user)):
    if user["status"] != "moderator":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Moderator privileges required.",
        )
    return user


def require_active_user(user=Depends(get_current_user)):
    if user["status"] == "nieaktywowany":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is not activated.",
        )
    return user


def pagination_params(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> dict:
    # Wspólna konwencja stronicowania dla wszystkich list (events, users, ...)
    return {"limit": limit, "offset": offset}
