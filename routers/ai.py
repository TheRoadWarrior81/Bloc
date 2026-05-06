from fastapi import APIRouter, Depends, HTTPException, Query
from auth import verify_token
from auth import verify_token, get_db, release_db
from services.embeddings import search_messages

router = APIRouter(prefix="/circles", tags=["ai"])


def is_member(circle_id: int, user_id: int) -> bool:
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM user_circles WHERE circle_id = %s AND user_id = %s",
                (circle_id, user_id),
            )
            return cur.fetchone() is not None
    finally:
        release_db(conn)


@router.get("/{circle_id}/search")
def semantic_search(
    circle_id: int,
    q: str = Query(..., min_length=1, max_length=500),
    current_user=Depends(verify_token),
):
    if not is_member(circle_id, current_user["user_id"]):
        raise HTTPException(status_code=403, detail="Not a member of this circle")

    results = search_messages(query=q, circle_id=circle_id)
    return {"query": q, "results": results}
