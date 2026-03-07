from dotenv import load_dotenv
load_dotenv()

from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException, Header, Depends
from pydantic import BaseModel
from typing import Optional
import psycopg2
import bcrypt
import jwt
import os
from datetime import datetime, timedelta
from fastapi.security import HTTPBearer


security = HTTPBearer()


app  = FastAPI()
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
    name: str
    invite_code: str

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

@app.get("/circles")
def get_circles(user=Depends(verify_token)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, invite_code, created_at FROM circles;")
    rows = cursor.fetchall()
    conn.close()

    circles = []
    for row in rows:
        circles.append({
            "id": row[0],
            "name": row[1],
            "invite_code": row[2],
            "created_at": row[3]
        })

    return {"circles": circles}

@app.post("/circles")
def create_circle(circle: CircleCreate, user=Depends(verify_token)):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("INSERT INTO circles (name, invite_code) VALUES (%s, %s) RETURNING id, name, invite_code;",
        (circle.name, circle.invite_code))
    
    new_circle = cursor.fetchone()
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
    username: str
    email: str
    password: str

@app.post("/users/register")
def register(user: UserRegister):
    # Hash the password
    password_hash = bcrypt.hashpw(
        user.password.encode('utf-8'), 
        bcrypt.gensalt()
    ).decode('utf-8')
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute(
        "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s) RETURNING id, username, email;",
        (user.username, user.email, password_hash)
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
    email: str
    password: str

@app.post("/users/login")
def login(user: UserLogin):
    conn  = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id, username, email, password_hash FROM users WHERE email = %s;" , (user.email,))
    row  = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check password against hash
    password_matches = bcrypt.checkpw(
        user.password.encode('utf-8'),
        row[3].encode('utf-8')
    )

    if not password_matches:
        raise HTTPException(status_code=401, detail="Wrong password")
    
    #Creat JWT token
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

    # Check the circle exists
    cursor.execute("SELECT id FROM circles WHERE id = %s;", (circle_id,))
    circle = cursor.fetchone()

    if not circle:
        conn.close()
        raise HTTPException(status_code=404, detail="Circle not found")

    # Add the connection
    cursor.execute(
        "INSERT INTO user_circles (user_id, circle_id) VALUES (%s, %s);",
        (user["user_id"], circle_id)
    )

    conn.commit()
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

    # Check circle exists
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

    return {"members": members}

@app.post("/circles/join-by-code")
def join_by_code(invite_code: str, user=Depends(verify_token)):
    conn = get_db()
    cursor = conn.cursor()

    try:
        # Find the circle with this invite code
        cursor.execute("SELECT id FROM circles WHERE invite_code = %s;", (invite_code,))
        circle = cursor.fetchone()

        if not circle:
            raise HTTPException(status_code=404, detail="Invalid invite code")

        circle_id = circle[0]

        # Join it - Using your suggested fix
        try:
            cursor.execute(
                "INSERT INTO user_circles (user_id, circle_id) VALUES (%s, %s);",
                (user["user_id"], circle_id)
            )
            conn.commit()
        except Exception:
            # If the insert fails (usually due to a duplicate), we roll back and raise 400
            conn.rollback()
            raise HTTPException(status_code=400, detail="Already in this circle")

        return {"message": f"Joined circle {circle_id}"}

    finally:
        # Always close the connection, regardless of success or failure
        conn.close()
