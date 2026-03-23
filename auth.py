import os
import jwt
import psycopg2
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

DB_URL = os.getenv("DB_URL")
JWT_SECRET = os.getenv("JWT_SECRET")

def get_db():
    return psycopg2.connect(DB_URL)

def verify_token(credentials=Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")