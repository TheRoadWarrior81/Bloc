import bcrypt
import jwt
import os
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from auth import get_db, verify_token, JWT_SECRET
from models import UserRegister, UserLogin, UserUpdate

limiter = Limiter(key_func=get_remote_address)
router = APIRouter()

RATE_LIMIT = os.getenv("RATE_LIMIT", "5/minute")
@router.post("/users/register")
@limiter.limit(RATE_LIMIT)
def register(request: Request, body: UserRegister):
    password_hash = bcrypt.hashpw(
        body.password.encode('utf-8'),
        bcrypt.gensalt()
    ).decode('utf-8')
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s) RETURNING id, username, email;",
        (body.username, body.email, password_hash)
    )
    new_user = cursor.fetchone()
    conn.commit()
    conn.close()
    return {"id": new_user[0], "username": new_user[1], "email": new_user[2]}

@router.post("/users/login")
@limiter.limit(RATE_LIMIT)
def login(request: Request, body: UserLogin):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, email, password_hash FROM users WHERE email = %s;", (body.email,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    if not bcrypt.checkpw(body.password.encode('utf-8'), row[3].encode('utf-8')):
        raise HTTPException(status_code=401, detail="Wrong password")
    token = jwt.encode(
        {"user_id": row[0], "username": row[1], "exp": datetime.utcnow() + timedelta(days=7)},
        JWT_SECRET,
        algorithm="HS256"
    )
    return {"token": token, "user_id": row[0], "username": row[1]}

@router.get("/users/me")
def get_me(user=Depends(verify_token)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, email FROM users WHERE id = %s;", (user["user_id"],))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    return {"id": row[0], "username": row[1], "email": row[2]}

@router.patch("/users/me")
def update_me(update: UserUpdate, user=Depends(verify_token)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET username = %s WHERE id = %s RETURNING id, username, email;",
        (update.username, user["user_id"])
    )
    updated = cursor.fetchone()
    conn.commit()
    conn.close()
    return {"id": updated[0], "username": updated[1], "email": updated[2]}

@router.get("/users/me/circles")
def get_my_circles(user=Depends(verify_token)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT circles.id, circles.name, circles.invite_code, user_circles.joined_at
        FROM circles
        JOIN user_circles ON circles.id = user_circles.circle_id
        WHERE user_circles.user_id = %s;
    """, (user["user_id"],))
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "name": r[1], "invite_code": r[2], "joined_at": r[3]} for r in rows]