import random
import string
from fastapi import APIRouter, HTTPException, Depends
from auth import get_db, verify_token
from bloc_logger import get_logger
from models import CircleCreate, JoinByCode, TransferAdminRequest

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
    cursor.execute("INSERT INTO user_circles (user_id, circle_id, role) VALUES (%s, %s, %s);",
        (user["user_id"], new_circle[0], "admin"))
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
        SELECT users.id, users.username, user_circles.joined_at, user_circles.role
        FROM users
        JOIN user_circles ON users.id = user_circles.user_id
        WHERE user_circles.circle_id = %s;
    """, (circle_id,))
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "username": r[1], "joined_at": r[2], "role": r[3]} for r in rows]

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

    # Check if requester is admin
    cursor.execute(
        "SELECT role FROM user_circles WHERE circle_id = %s AND user_id = %s",
        (circle_id, user["user_id"])
    )
    row = cursor.fetchone()
    if row and row[0] == "admin":
        # Check if other members exist
        cursor.execute(
            "SELECT COUNT(*) FROM user_circles WHERE circle_id = %s AND user_id != %s",
            (circle_id, user["user_id"])
        )
        count = cursor.fetchone()[0]
        if count > 0:
            conn.close()
            raise HTTPException(status_code=400, detail="Transfer admin to another member before leaving")

    # Delete membership
    cursor.execute(
        "DELETE FROM user_circles WHERE user_id = %s AND circle_id = %s",
        (user["user_id"], circle_id)
    )
    if cursor.rowcount == 0:
        conn.close()
        logger.warning(f"leave failed — not a member user_id={user['user_id']} circle_id={circle_id}")
        raise HTTPException(status_code=404, detail="You are not in this circle")

    conn.commit()

    # Auto-delete bloc if no members left
    cursor.execute("SELECT COUNT(*) FROM user_circles WHERE circle_id = %s", (circle_id,))
    remaining = cursor.fetchone()[0]
    if remaining == 0:
        cursor.execute("DELETE FROM circles WHERE id = %s", (circle_id,))
        conn.commit()
        logger.info(f"bloc auto-deleted — no members left circle_id={circle_id}")

    conn.close()
    logger.info(f"user left circle user_id={user['user_id']} circle_id={circle_id}")
    return {"message": "Left circle successfully"}

@router.delete("/circles/{circle_id}/members/{target_user_id}")
def kick_member(circle_id: int, target_user_id: int, user=Depends(verify_token)):
    conn = get_db()
    cursor = conn.cursor()

    # Check requester is admin
    cursor.execute(
        "SELECT role FROM user_circles WHERE circle_id = %s AND user_id = %s;",
        (circle_id, user["user_id"])
    )
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=403, detail="You are not in this circle")
    if row[0] != "admin":
        conn.close()
        raise HTTPException(status_code=403, detail="Only admins can kick members")

    # Can't kick yourself
    if target_user_id == user["user_id"]:
        conn.close()
        raise HTTPException(status_code=400, detail="You cannot kick yourself — use leave instead")

    # Kick the target
    cursor.execute(
        "DELETE FROM user_circles WHERE user_id = %s AND circle_id = %s;",
        (target_user_id, circle_id)
    )
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="User is not in this circle")
    conn.commit()
    conn.close()
    logger.info(f"member kicked circle_id={circle_id} target_user_id={target_user_id} by admin_user_id={user['user_id']}")
    return {"message": f"User {target_user_id} removed from circle"}

@router.delete("/circles/{circle_id}")
def delete_circle(circle_id: int, user=Depends(verify_token)):
    conn = get_db()
    cursor = conn.cursor()

    # Check requester is admin
    cursor.execute(
        "SELECT role FROM user_circles WHERE circle_id = %s AND user_id = %s;",
        (circle_id, user["user_id"])
    )
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=403, detail="You are not in this circle")
    if row[0] != "admin":
        conn.close()
        raise HTTPException(status_code=403, detail="Only admins can delete a bloc")

    # Delete the circle — cascades to user_circles and messages
    cursor.execute("DELETE FROM circles WHERE id = %s;", (circle_id,))
    conn.commit()
    conn.close()
    logger.info(f"circle deleted circle_id={circle_id} by admin_user_id={user['user_id']}")
    return {"message": "Bloc deleted"}

@router.patch("/circles/{circle_id}/transfer-admin")
def transfer_admin(circle_id: int, body: TransferAdminRequest, user=Depends(verify_token)):
    conn = get_db()
    cur = conn.cursor()

    # Check requester is admin
    cur.execute(
        "SELECT role FROM user_circles WHERE circle_id = %s AND user_id = %s",
        (circle_id, user["user_id"])
    )
    row = cur.fetchone()
    if not row or row[0] != "admin":
        conn.close()
        raise HTTPException(status_code=403, detail="Only admins can transfer ownership")

    # Check target is a member
    cur.execute(
        "SELECT role FROM user_circles WHERE circle_id = %s AND user_id = %s",
        (circle_id, body.new_admin_id)
    )
    target = cur.fetchone()
    if not target:
        conn.close()
        raise HTTPException(status_code=404, detail="Target user is not a member of this bloc")

    # Transfer
    cur.execute(
        "UPDATE user_circles SET role = 'member' WHERE circle_id = %s AND user_id = %s",
        (circle_id, user["user_id"])
    )
    cur.execute(
        "UPDATE user_circles SET role = 'admin' WHERE circle_id = %s AND user_id = %s",
        (circle_id, body.new_admin_id)
    )
    conn.commit()
    conn.close()

    logger.info(f"transfer_admin circle_id={circle_id} from={user['user_id']} to={body.new_admin_id}")
    return {"message": "Admin transferred successfully"}
