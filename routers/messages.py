import jwt
from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect
from auth import get_db, verify_token
from config import settings
from bloc_logger import get_logger

logger = get_logger("messages")
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
        if circle_id in self.active_connections:
            try:
                self.active_connections[circle_id].remove(websocket)
            except ValueError:
                pass  # already removed, safe to ignore

    async def broadcast(self, circle_id: int, message: dict):
        if circle_id in self.active_connections:
            dead = []
            for connection in self.active_connections[circle_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    dead.append(connection)
            # Clean up any connections that died mid-broadcast
            for connection in dead:
                self.disconnect(circle_id, connection)


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
    try:
        cur.execute(
            "SELECT 1 FROM user_circles WHERE circle_id = %s AND user_id = %s",
            (circle_id, user["user_id"])
        )
        if not cur.fetchone():
            logger.warning(f"message send denied — not a member user_id={user['user_id']} circle_id={circle_id}")
            raise HTTPException(status_code=403, detail="Not a member of this circle")

        cur.execute(
            "INSERT INTO messages (circle_id, user_id, content) VALUES (%s, %s, %s) RETURNING id, created_at",
            (circle_id, user["user_id"], content)
        )
        row = cur.fetchone()
        conn.commit()
        logger.info(f"message sent circle_id={circle_id} user_id={user['user_id']} msg_id={row[0]}")
        return {
            "id": row[0], "circle_id": circle_id, "user_id": user["user_id"],
            "username": user["username"], "content": content, "created_at": str(row[1])
        }
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        logger.error(f"send_message failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to send message")
    finally:
        cur.close()
        conn.close()


@router.get("/circles/{circle_id}/messages")
def get_messages(
    circle_id: int,
    limit: int = 50,
    before: int = None,
    user=Depends(verify_token)
):
    conn = get_db()
    cur = conn.cursor()
    try:
        # Membership check
        cur.execute(
            "SELECT 1 FROM user_circles WHERE circle_id = %s AND user_id = %s",
            (circle_id, user["user_id"])
        )
        if not cur.fetchone():
            logger.warning(f"messages fetch denied — not a member user_id={user['user_id']} circle_id={circle_id}")
            raise HTTPException(status_code=403, detail="Not a member of this circle")

        if before:
            cur.execute("""
                SELECT m.id, m.circle_id, m.user_id, u.username, m.content, m.created_at
                FROM messages m
                JOIN users u ON m.user_id = u.id
                WHERE m.circle_id = %s AND m.id < %s
                ORDER BY m.created_at DESC
                LIMIT %s
            """, (circle_id, before, limit))
        else:
            cur.execute("""
                SELECT m.id, m.circle_id, m.user_id, u.username, m.content, m.created_at
                FROM messages m
                JOIN users u ON m.user_id = u.id
                WHERE m.circle_id = %s
                ORDER BY m.created_at DESC
                LIMIT %s
            """, (circle_id, limit))

        rows = cur.fetchall()
        rows.reverse()

        return [
            {
                "id": r[0], "circle_id": r[1], "user_id": r[2],
                "username": r[3], "content": r[4], "created_at": str(r[5])
            }
            for r in rows
        ]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"get_messages failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch messages")
    finally:
        cur.close()
        conn.close()


@router.websocket("/circles/{circle_id}/ws")
async def websocket_endpoint(circle_id: int, websocket: WebSocket, token: str):
    # Verify JWT before accepting the connection
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        user = payload
    except jwt.InvalidTokenError:
        logger.warning(f"websocket rejected — invalid token circle_id={circle_id}")
        await websocket.close(code=1008)
        return

    # Verify user is a member of this circle
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT 1 FROM user_circles WHERE circle_id = %s AND user_id = %s",
            (circle_id, user["user_id"])
        )
        if not cur.fetchone():
            logger.warning(f"websocket rejected — not a member user_id={user['user_id']} circle_id={circle_id}")
            await websocket.close(code=1008)
            return
    finally:
        cur.close()
        conn.close()

    logger.info(f"websocket connected user_id={user['user_id']} circle_id={circle_id}")
    await manager.connect(circle_id, websocket)

    try:
        while True:
            data = await websocket.receive_json()
            content = data.get("content", "").strip()
            if not content or len(content) > 1000:
                continue

            conn = get_db()
            cur = conn.cursor()
            try:
                cur.execute(
                    "INSERT INTO messages (circle_id, user_id, content) VALUES (%s, %s, %s) RETURNING id, created_at",
                    (circle_id, user["user_id"], content)
                )
                row = cur.fetchone()
                conn.commit()
                logger.info(f"websocket message circle_id={circle_id} user_id={user['user_id']} msg_id={row[0]}")
                await manager.broadcast(circle_id, {
                    "id": row[0], "circle_id": circle_id, "user_id": user["user_id"],
                    "username": user["username"], "content": content, "created_at": str(row[1])
                })
            except Exception as e:
                conn.rollback()
                logger.error(f"websocket message insert failed: {e}")
            finally:
                cur.close()
                conn.close()

    except WebSocketDisconnect:
        manager.disconnect(circle_id, websocket)
        logger.info(f"websocket disconnected user_id={user['user_id']} circle_id={circle_id}")
    except Exception as e:
        manager.disconnect(circle_id, websocket)
        logger.error(f"websocket error user_id={user['user_id']} circle_id={circle_id}: {e}")
