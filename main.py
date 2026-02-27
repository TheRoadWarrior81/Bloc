from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from pydantic import BaseModel
import psycopg2
import bcrypt
import jwt
import os
from datetime import datetime, timedelta


app  = FastAPI()

DB_URL = os.getenv("DB_URL")
JWT_SECRET = os.getenv("JWT_SECRET")

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
def get_circles():
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
def create_circle(circle: CircleCreate):
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
    return {"error": "Circle not found"}, 404

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
        return {"error": "User not found"}, 404
    
    # Check password against hash
    password_matches = bcrypt.checkpw(
        user.password.encode('utf-8'),
        row[3].encode('utf-8')
    )

    if not password_matches:
        return {"error": "Wrong password"}, 401
    
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

    return {"token": token}
