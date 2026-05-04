import asyncio
import jwt
from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect
from auth import get_db, release_db, verify_token
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
                pass

    async def broadcast(self, circle_id: int, message: dict):
        if circle_id in self.active_connections:
            dead = []
            for connection in self.active_connections[circle_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    dead.append(connection)
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
        release_db(conn)                  # ← return to pool


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
        release_db(conn)                  # ← return to pool


@router.websocket("/circles/{circle_id}/ws")
async def websocket_endpoint(circle_id: int, websocket: WebSocket):
    # Step 1: accept the raw connection — no token in the URL
    await websocket.accept()

    # Step 2: wait up to 10 seconds for the client to send an auth frame.
    # Expected shape: {"type": "auth", "token": "<jwt>"}
    # If it doesn't arrive in time, or is malformed, close immediately.
    try:
        auth_data = await asyncio.wait_for(websocket.receive_json(), timeout=10.0)
    except (asyncio.TimeoutError, Exception):
        logger.warning(f"websocket closed — no auth frame received circle_id={circle_id}")
        await websocket.close(code=1008)
        return

    if auth_data.get("type") != "auth":
        logger.warning(f"websocket closed — first frame was not auth circle_id={circle_id}")
        await websocket.close(code=1008)
        return

    # Step 3: validate the JWT from the auth frame
    token = auth_data.get("token", "")
    try:
        user = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
    except jwt.InvalidTokenError:
        logger.warning(f"websocket closed — invalid token circle_id={circle_id}")
        await websocket.close(code=1008)
        return

    # Step 4: check revoked tokens (same as verify_token in auth.py)
    jti = user.get("jti")
    if jti:
        conn = get_db()
        cur = conn.cursor()
        try:
            cur.execute("SELECT 1 FROM revoked_tokens WHERE jti = %s", (jti,))
            if cur.fetchone():
                logger.warning(f"websocket closed — revoked token user_id={user.get('user_id')} circle_id={circle_id}")
                await websocket.close(code=1008)
                return
        finally:
            cur.close()
            release_db(conn)

    # Step 5: membership check
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT 1 FROM user_circles WHERE circle_id = %s AND user_id = %s",
            (circle_id, user["user_id"])
        )
        if not cur.fetchone():
            logger.warning(f"websocket closed — not a member user_id={user['user_id']} circle_id={circle_id}")
            await websocket.close(code=1008)
            return
    finally:
        cur.close()
        release_db(conn)

    logger.info(f"websocket connected user_id={user['user_id']} circle_id={circle_id}")
    manager.active_connections.setdefault(circle_id, []).append(websocket)

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
                release_db(conn)          # ← return to pool

    except WebSocketDisconnect:
        manager.disconnect(circle_id, websocket)
        logger.info(f"websocket disconnected user_id={user['user_id']} circle_id={circle_id}")
    except Exception as e:
        manager.disconnect(circle_id, websocket)
        logger.error(f"websocket error user_id={user['user_id']} circle_id={circle_id}: {e}")