from collections.abc import Generator

from psycopg2 import pool
from psycopg2.extras import RealDictCursor

from config import settings

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
