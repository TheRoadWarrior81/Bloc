import jwt
from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect
from auth import get_db, verify_token, JWT_SECRET

router = APIRouter()

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

@router.post("/circles/{circle_id}/messages")
def send_message(circle_id: int, body: dict, user=Depends(verify_token)):
    content = body.get("content", "").strip()
    if not content:
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    if len(content) > 1000:
        raise HTTPException(status_code=400, detail="Message too long")
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
    return {"id": row[0], "circle_id": circle_id, "user_id": user["user_id"],
            "username": user["username"], "content": content, "created_at": str(row[1])}

@router.get("/circles/{circle_id}/messages")
def get_messages(circle_id: int, user=Depends(verify_token)):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT m.id, m.circle_id, m.user_id, u.username, m.content, m.created_at
        FROM messages m
        JOIN users u ON m.user_id = u.id
        WHERE m.circle_id = %s
        ORDER BY m.created_at ASC
        """, (circle_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{"id": r[0], "circle_id": r[1], "user_id": r[2], "username": r[3],
             "content": r[4], "created_at": str(r[5])} for r in rows]

@router.websocket("/circles/{circle_id}/ws")
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
            await manager.broadcast(circle_id, {
                "id": row[0], "circle_id": circle_id, "user_id": user["user_id"],
                "username": user["username"], "content": content, "created_at": str(row[1])
            })
    except WebSocketDisconnect:
        manager.disconnect(circle_id, websocket)