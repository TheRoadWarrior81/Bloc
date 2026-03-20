import os
import pytest
import psycopg2
from dotenv import load_dotenv

# Load test env vars BEFORE importing the app
load_dotenv(".env.test", override=True)

from fastapi.testclient import TestClient
from main import app, get_db

@pytest.fixture(scope="session")
def db():
    """One real DB connection for the whole test session."""
    conn = psycopg2.connect(os.getenv("DB_URL"))
    yield conn
    conn.close()

@pytest.fixture(autouse=True)
def clean_db(db):
    """Wipe all tables before every single test. Runs automatically."""
    yield
    cur = db.cursor()
    # Delete in order that respects foreign keys
    cur.execute("DELETE FROM messages;")
    cur.execute("DELETE FROM user_circles;")
    cur.execute("DELETE FROM circles;")
    cur.execute("DELETE FROM users;")
    db.commit()
    cur.close()

@pytest.fixture(scope="session")
def client():
    return TestClient(app)