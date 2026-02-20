from fastapi import FastAPI
from pydantic import BaseModel
import psycopg2

app  = FastAPI()

DB_URL = "postgresql://neondb_owner:npg_eWMXFtv2b9Ai@ep-super-silence-aibswe2u-pooler.c-4.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

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