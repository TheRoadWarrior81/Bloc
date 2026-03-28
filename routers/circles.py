import random
import string
from fastapi import APIRouter, HTTPException, Depends
from auth import get_db, verify_token
from models import CircleCreate, JoinByCode
from bloc_logger import get_logger

logger = get_logger("circles")
router = APIRouter()

@router.post("/circles")
def create_circle(circle: CircleCreate, user=Depends(verify_token)):
    conn = get_db()
    cursor = conn.cursor()
    invite_code = circle.invite_code or ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    cursor.execute(
        "INSERT INTO circles (name, invite_code) VALUES (%s, %s) RETURNING id, name, invite_code;",
        (circle.name, invite_code)
    )
    new_circle = cursor.fetchone()
    cursor.execute("INSERT INTO user_circles (user_id, circle_id) VALUES (%s, %s);",
        (user["user_id"], new_circle[0]))
    conn.commit()
    conn.close()
    logger.info(f"circle created circle_id={new_circle[0]} user_id={user['user_id']}")
    return {"id": new_circle[0], "name": new_circle[1], "invite_code": new_circle[2]}

@router.get("/circles/{circle_id}")
def get_circle(circle_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, invite_code, created_at FROM circles WHERE id = %s;", (circle_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"id": row[0], "name": row[1], "invite_code": row[2], "created_at": row[3]}
    logger.warning(f"circle not found circle_id={circle_id}")
    raise HTTPException(status_code=404, detail="Circle not found")

@router.get("/circles/{circle_id}/members")
def get_circle_members(circle_id: int, user=Depends(verify_token)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM circles WHERE id = %s;", (circle_id,))
    if not cursor.fetchone():
        conn.close()
        logger.warning(f"members fetch failed — circle not found circle_id={circle_id}")
        raise HTTPException(status_code=404, detail="Circle not found")
    cursor.execute("""
        SELECT users.id, users.username, user_circles.joined_at
        FROM users
        JOIN user_circles ON users.id = user_circles.user_id
        WHERE user_circles.circle_id = %s;
    """, (circle_id,))
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "username": r[1], "joined_at": r[2]} for r in rows]

@router.post("/circles/{circle_id}/join")
def join_circle(circle_id: int, user=Depends(verify_token)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM circles WHERE id = %s;", (circle_id,))
    if not cursor.fetchone():
        conn.close()
        logger.warning(f"join failed — circle not found circle_id={circle_id}")
        raise HTTPException(status_code=404, detail="Circle not found")
    try:
        cursor.execute("INSERT INTO user_circles (user_id, circle_id) VALUES (%s, %s);",
            (user["user_id"], circle_id))
        conn.commit()
        logger.info(f"user joined circle user_id={user['user_id']} circle_id={circle_id}")
    except Exception:
        conn.rollback()
        logger.warning(f"join failed — already a member user_id={user['user_id']} circle_id={circle_id}")
        raise HTTPException(status_code=400, detail="Already in this circle")
    finally:
        conn.close()
    return {"message": f"Joined circle {circle_id}"}

@router.post("/circles/join-by-code")
def join_by_code(body: JoinByCode, user=Depends(verify_token)):
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM circles WHERE invite_code = %s;", (body.invite_code,))
        circle = cursor.fetchone()
        if not circle:
            logger.warning(f"join-by-code failed — invalid code user_id={user['user_id']}")
            raise HTTPException(status_code=404, detail="Invalid invite code")
        try:
            cursor.execute("INSERT INTO user_circles (user_id, circle_id) VALUES (%s, %s);",
                (user["user_id"], circle[0]))
            conn.commit()
            logger.info(f"user joined by code user_id={user['user_id']} circle_id={circle[0]}")
        except Exception:
            conn.rollback()
            logger.warning(f"join-by-code failed — already a member user_id={user['user_id']} circle_id={circle[0]}")
            raise HTTPException(status_code=400, detail="Already in this circle")
        return {"message": f"Joined circle {circle[0]}"}
    finally:
        conn.close()

@router.delete("/circles/{circle_id}/leave")
def leave_circle(circle_id: int, user=Depends(verify_token)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_circles WHERE user_id = %s AND circle_id = %s;",
        (user["user_id"], circle_id))
    if cursor.rowcount == 0:
        conn.close()
        logger.warning(f"leave failed — not a member user_id={user['user_id']} circle_id={circle_id}")
        raise HTTPException(status_code=404, detail="You are not in this circle")
    conn.commit()
    conn.close()
    logger.info(f"user left circle user_id={user['user_id']} circle_id={circle_id}")
    return {"message": "Left circle successfully"}