import jwt
import psycopg2
import psycopg2.pool
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer
from config import settings

security = HTTPBearer()

_pool = psycopg2.pool.ThreadedConnectionPool(
    minconn=1,
    maxconn=5,
    dsn=settings.DB_URL,
    keepalives=1,
    keepalives_idle=30,
    keepalives_interval=10,
    keepalives_count=5
)

def get_db():
    conn = _pool.getconn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.close()
    except Exception:
        try:
            _pool.putconn(conn, close=True)
        except Exception:
            pass
        conn = _pool.getconn()
    return conn

def release_db(conn):
    """Return a connection to the pool instead of closing it."""
    try:
        cur = conn.cursor()
        cur.execute("RESET app.current_user_id")
        cur.close()
    except Exception:
        pass
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
                release_db(conn)

        return payload
    except HTTPException:
        raise
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_db_scoped(user=Depends(verify_token)):
    """
    Same as get_db(), but sets app.current_user_id on the connection
    so RLS policies can scope every query to the authenticated user.
    """
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("SET app.current_user_id = %s", (str(user["user_id"]),))
    finally:
        cur.close()
    return conn