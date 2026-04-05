import jwt
import psycopg2
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer
from config import settings

security = HTTPBearer()


def get_db():
    return psycopg2.connect(settings.DB_URL)


def verify_token(credentials=Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])

        # Check if this token has been revoked (e.g. user logged out)
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
                conn.close()

        return payload
    except HTTPException:
        raise
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")