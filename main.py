from dotenv import load_dotenv
load_dotenv()

from pydantic import BaseModel, Field
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException, Header, Depends, Request
from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from typing import Optional
import psycopg2
import bcrypt
import jwt
import os
import random
import string
from datetime import datetime, timedelta
from fastapi.security import HTTPBearer


security = HTTPBearer()


app  = FastAPI()
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://bloc-join-gather.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_URL = os.getenv("DB_URL")
JWT_SECRET = os.getenv("JWT_SECRET")


def verify_token(credentials=Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_db():
    conn = psycopg2.connect(DB_URL)
    return conn

class CircleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    invite_code: str | None = Field(default=None, max_length=20)

class JoinByCode(BaseModel):
    invite_code: str = Field(min_length=1, max_length=20)


@app.get("/hello")
def hello():
    return {"message": "hello world"}

@app.get("/test-db")
def test_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT current_database(), current_user;")
    result = cursor.fetchone()
    conn.close()
    return {"database": result[0], "user": result[1]}

@app.post("/circles")
def create_circle(circle: CircleCreate, user=Depends(verify_token)):
    conn = get_db()
    cursor = conn.cursor()
    
    invite_code = circle.invite_code or ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    
    cursor.execute("INSERT INTO circles (name, invite_code) VALUES (%s, %s) RETURNING id, name, invite_code;",
        (circle.name, invite_code))
    new_circle = cursor.fetchone()

    cursor.execute("INSERT INTO user_circles (user_id, circle_id) VALUES (%s, %s);",
        (user["user_id"], new_circle[0]))

    conn.commit()
    conn.close()
    return {
        "id": new_circle[0],
        "name": new_circle[1],
        "invite_code": new_circle[2]
    }

@app.get("/circles/{circle_id}")
def get_circle(circle_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, invite_code, created_at FROM circles WHERE id = %s;", (circle_id,))
    row = cursor.fetchone()
    conn.close()
    if row:        
        return {
            "id": row[0],
            "name": row[1],
            "invite_code": row[2],
            "created_at": row[3]
        }
    raise HTTPException(status_code=404, detail="Circle not found")

class UserRegister(BaseModel):
    username: str = Field(min_length=2, max_length=30)
    email: str = Field(max_length=100)
    password: str = Field(min_length=6, max_length=72)

@app.post("/users/register")
@limiter.limit("5/minute")
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
    
    return {
        "id": new_user[0],
        "username": new_user[1],
        "email": new_user[2]
    }

class UserLogin(BaseModel):
    email: str = Field(max_length=100)
    password: str = Field(min_length=6, max_length=72)

@app.post("/users/login")
@limiter.limit("5/minute")
def login(request: Request, body: UserLogin):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id, username, email, password_hash FROM users WHERE email = %s;", (body.email,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    
    password_matches = bcrypt.checkpw(
        body.password.encode('utf-8'),
        row[3].encode('utf-8')
    )

    if not password_matches:
        raise HTTPException(status_code=401, detail="Wrong password")
    
    token = jwt.encode(
        {
            "user_id": row[0],
            "username": row[1],
            "exp": datetime.utcnow() + timedelta(days=7)
        },
        JWT_SECRET,
        algorithm="HS256"
    )

    return {"token": token, "user_id": row[0], "username": row[1]}

@app.get("/users/me")
def get_me(user=Depends(verify_token)):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT id, username, email FROM users WHERE id = %s;",
        (user["user_id"],)
    )
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": row[0],
        "username": row[1],
        "email": row[2]
    }

@app.post("/circles/{circle_id}/join")
def join_circle(circle_id: int, user=Depends(verify_token)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM circles WHERE id = %s;", (circle_id,))
    circle = cursor.fetchone()
    if not circle:
        conn.close()
        raise HTTPException(status_code=404, detail="Circle not found")
    try:
        cursor.execute(
            "INSERT INTO user_circles (user_id, circle_id) VALUES (%s, %s);",
            (user["user_id"], circle_id)
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise HTTPException(status_code=400, detail="Already in this circle")
    finally:
        conn.close()
    return {"message": f"Joined circle {circle_id}"}

@app.get("/users/me/circles")
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

    circles = []
    for row in rows:
        circles.append({
            "id": row[0],
            "name": row[1],
            "invite_code": row[2],
            "joined_at": row[3]
        })

    return circles

@app.get("/circles/{circle_id}/members")
def get_circle_members(circle_id: int, user=Depends(verify_token)):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM circles WHERE id = %s;", (circle_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Circle not found")

    cursor.execute("""
        SELECT users.id, users.username, user_circles.joined_at
        FROM users
        JOIN user_circles ON users.id = user_circles.user_id
        WHERE user_circles.circle_id = %s;
    """, (circle_id,))

    rows = cursor.fetchall()
    conn.close()

    members = []
    for row in rows:
        members.append({
            "id": row[0],
            "username": row[1],
            "joined_at": row[2]
        })

    return members

@app.post("/circles/join-by-code")
def join_by_code(body: JoinByCode, user=Depends(verify_token)):
    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT id FROM circles WHERE invite_code = %s;", (body.invite_code,))
        circle = cursor.fetchone()

        if not circle:
            raise HTTPException(status_code=404, detail="Invalid invite code")

        circle_id = circle[0]

        try:
            cursor.execute(
                "INSERT INTO user_circles (user_id, circle_id) VALUES (%s, %s);",
                (user["user_id"], circle_id)
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise HTTPException(status_code=400, detail="Already in this circle")

        return {"message": f"Joined circle {circle_id}"}

    finally:
        conn.close()

@app.delete("/circles/{circle_id}/leave")
def leave_circle(circle_id: int, user=Depends(verify_token)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM user_circles WHERE user_id = %s AND circle_id = %s;",
        (user["user_id"], circle_id)
    )
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="You are not in this circle")
    conn.commit()
    conn.close()
    return {"message": "Left circle successfully"}
        
class UserUpdate(BaseModel):
    username: str

@app.patch("/users/me")
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
    return {
        "id": updated[0],
        "username": updated[1],
        "email": updated[2]
    }
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[int, list[WebSocket]] = {}

    async def connect(self, circle_id: int, websocket: WebSocket):
        await websocket.accept()
        if circle_id not in self.active_connections:
            self.active_connections[circle_id] = []
        self.active_connections[circle_id].append(websocket)

    def disconnect(self, circle_id: int, websocket: WebSocket):
        self.active_connections[circle_id].remove(websocket)

    async def broadcast(self, circle_id: int, message: dict):
        if circle_id in self.active_connections:
            for connection in self.active_connections[circle_id]:
                await connection.send_json(message)

manager = ConnectionManager()
# Send a message
@app.post("/circles/{circle_id}/messages")
def send_message(circle_id: int, body: dict, user=Depends(verify_token)):
    content = body.get("content", "").strip()
    if not content:
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO messages (circle_id, user_id, content) VALUES (%s, %s, %s) RETURNING id, created_at",
        (circle_id, user["user_id"], content)
    )
    row = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return {
        "id": row[0],
        "circle_id": circle_id,
        "user_id": user["user_id"],
        "username": user["username"],
        "content": content,
        "created_at": str(row[1])
    }


# Get message history
@app.get("/circles/{circle_id}/messages")
def get_messages(circle_id: int, user=Depends(verify_token)):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT m.id, m.circle_id, m.user_id, u.username, m.content, m.created_at
        FROM messages m
        JOIN users u ON m.user_id = u.id
        WHERE m.circle_id = %s
        ORDER BY m.created_at ASC
        """,
        (circle_id,)
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [
        {
            "id": r[0],
            "circle_id": r[1],
            "user_id": r[2],
            "username": r[3],
            "content": r[4],
            "created_at": str(r[5])
        }
        for r in rows
    ]


# WebSocket for real-time chat
@app.websocket("/circles/{circle_id}/ws")
async def websocket_endpoint(circle_id: int, websocket: WebSocket, token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user = payload
    except jwt.InvalidTokenError:
        await websocket.close(code=1008)
        return

    await manager.connect(circle_id, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            content = data.get("content", "").strip()
            if not content:
                continue

            # Save to database
            conn = get_db()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO messages (circle_id, user_id, content) VALUES (%s, %s, %s) RETURNING id, created_at",
                (circle_id, user["user_id"], content)
            )
            row = cur.fetchone()
            conn.commit()
            cur.close()
            conn.close()

            # Broadcast to everyone in the bloc
            await manager.broadcast(circle_id, {
                "id": row[0],
                "circle_id": circle_id,
                "user_id": user["user_id"],
                "username": user["username"],
                "content": content,
                "created_at": str(row[1])
            })
    except WebSocketDisconnect:
        manager.disconnect(circle_id, websocket)
