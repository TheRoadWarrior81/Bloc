import jwt
import psycopg2
import psycopg2.pool
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer
from config import settings

security = HTTPBearer()

# One pool shared across all requests.
# minconn=2 keeps warm connections ready; maxconn=10 prevents overwhelming Neon.
_pool = psycopg2.pool.ThreadedConnectionPool(
    minconn=2,
    maxconn=10,
    dsn=settings.DB_URL,
    keepalives=1,
    keepalives_idle=30,
    keepalives_interval=10,
    keepalives_count=5
)

def get_db():
    conn = _pool.getconn()
    try:
        conn.cursor().execute("SELECT 1")
    except Exception:
        # Connection is dead — discard it and get a fresh one
        _pool.putconn(conn, close=True)
        conn = psycopg2.connect(settings.DB_URL)
    return conn

def release_db(conn):
    """Return a connection to the pool instead of closing it."""
    _pool.putconn(conn)


def verify_token(credentials=Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])

        jti = payload.get("jti")
        if jti:
            conn = get_db()
            cur = conn.cursor()
            try:
                cur.execute(
                    "SELECT 1 FROM revoked_tokens WHERE jti = %s",
                    (jti,)
                )
                if cur.fetchone():
                    raise HTTPException(status_code=401, detail="Token has been revoked")
            finally:
                cur.close()
                release_db(conn)          # ← return to pool, not close

        return payload
    except HTTPException:
        raise
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")