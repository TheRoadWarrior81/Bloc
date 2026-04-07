import time
import sentry_sdk
from config import settings
from dotenv import load_dotenv
load_dotenv()

sentry_sdk.init(
    dsn=settings.SENTRY_DSN,
    traces_sample_rate=0.2,
    environment=settings.ENVIRONMENT
)

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from routers import users, circles, messages
from bloc_logger import get_logger

logger = get_logger("request")

app = FastAPI()

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

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000

    # Log every request with method, path, status, and latency
    # 4xx and 5xx get WARNING/ERROR so they surface immediately in Railway logs
    log_line = (
        f"method={request.method} "
        f"path={request.url.path} "
        f"status={response.status_code} "
        f"duration={duration_ms:.1f}ms"
    )

    if response.status_code >= 500:
        logger.error(log_line)
    elif response.status_code >= 400:
        logger.warning(log_line)
    else:
        logger.info(log_line)

    return response

app.include_router(users.router)
app.include_router(circles.router)
app.include_router(messages.router)

@app.get("/hello")
def hello():
    return {"message": "hello world"}

@app.get("/test-db")
def test_db():
    from auth import get_db
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT current_database(), current_user;")
    result = cursor.fetchone()
    conn.close()
    return {"database": result[0], "user": result[1]}