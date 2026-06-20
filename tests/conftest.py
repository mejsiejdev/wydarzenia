import os

import pytest
from dotenv import load_dotenv

load_dotenv()

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")
if TEST_DATABASE_URL is None:
    pytest.skip(
        "TEST_DATABASE_URL is not set; skipping integration tests.",
        allow_module_level=True,
    )

os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-at-least-32-bytes-long")

import psycopg2  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from psycopg2.extras import RealDictCursor  # noqa: E402

from dependencies import get_db  # noqa: E402
from main import app  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _migrate():
    # Budujemy schemat bazy testowej tymi samymi migracjami co produkcyjną.
    from alembic.config import Config

    from alembic import command

    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", TEST_DATABASE_URL)
    command.upgrade(config, "head")


@pytest.fixture
def db_conn():
    # Jedno połączenie na test: BEGIN ... ROLLBACK izoluje testy od siebie.
    conn = psycopg2.connect(TEST_DATABASE_URL, cursor_factory=RealDictCursor)
    conn.autocommit = False
    try:
        yield conn
    finally:
        conn.rollback()
        conn.close()


@pytest.fixture
def client(db_conn):
    # Podmieniamy get_db, żeby cała aplikacja korzystała z połączenia testowego.
    def override_get_db():
        cursor = db_conn.cursor()
        yield cursor

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def address_id(db_conn):
    # Lokacje wymagają istniejącego adresu (FK location_addresses).
    cursor = db_conn.cursor()
    cursor.execute(
        """
        INSERT INTO location_addresses (street, building_number, city, postal_code)
        VALUES ('Wybrzeże Wyspiańskiego', '27', 'Wrocław', '50-370')
        RETURNING id;
        """
    )
    return str(cursor.fetchone()["id"])
