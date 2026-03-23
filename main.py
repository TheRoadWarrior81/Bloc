import sentry_sdk
import os
from dotenv import load_dotenv
load_dotenv()
sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    traces_sample_rate=0.2,
    environment=os.getenv("ENVIRONMENT", "development")
)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from routers import users, circles, messages

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

