# CircleShift API

## What is this
A private social API for friend groups — users can create circles, join them via invite codes, and see who's in them.

## What I've built so far
- `GET /hello` — health check
- `GET /test-db` — confirms database connection
- `GET /circles` — list all circles (protected)
- `POST /circles` — create a circle (protected)
- `GET /circles/{id}` — get a single circle
- `GET /circles/{id}/members` — see who's in a circle (protected)
- `POST /circles/{id}/join` — join a circle by ID (protected)
- `POST /circles/join-by-code` — join a circle by invite code (protected)
- `POST /users/register` — create an account
- `POST /users/login` — login and get a JWT token
- `GET /users/me` — get your own profile (protected)
- `GET /users/me/circles` — list the circles you've joined (protected)

## Tech stack
- **Python + FastAPI** — already knew Python, FastAPI is fast to get routes working
- **PostgreSQL on Neon.tech** — Codespaces had permission issues with local postgres, Neon just works
- **GitHub Codespaces** — dev environment in the browser, no local setup
- **JWT + bcrypt** — industry standard auth, passwords hashed, tokens stateless
- **psycopg2** — connects Python to PostgreSQL

## What I learned building this
- How a FastAPI route connects to a database
- Why POST needs `conn.commit()` but GET doesn't
- What `RETURNING` does in a SQL INSERT
- Why passwords are hashed and how bcrypt works
- What a JWT token is, how to decode it, and that it's never stored in the database
- How to protect routes with `Depends()`
- How to use `.env` to keep secrets out of GitHub
- How to read tracebacks to find the actual error line
- What a junction table is and why many-to-many relationships need one
- How SQL JOINs work and how to use them in both directions
- The difference between `fetchone()` and `fetchall()`
- How to debug an empty API response by checking the database directly

## How to run it locally
```bash
# Activate virtual environment
source venv/bin/activate

# Start the server
uvicorn main:app --reload

# Check what's running on port 8000
lsof -i :8000
```

Then open `/docs` in your browser to test routes via Swagger UI.

Make sure your `.env` file has:
```
DB_URL=your_neon_connection_string
JWT_SECRET=your_secret_key
```

## Dev Log

### Session 1 — Feb 20 2026
**Built:** GET /circles, POST /circles, connected to Neon PostgreSQL
**Learned:**
- How a FastAPI route connects to a database
- Why POST needs conn.commit() but GET doesn't
- What RETURNING does in a SQL INSERT

**Stuck on:** PostgreSQL sudo permissions in Codespaces (solved by using Neon instead)
**Next session:** Build users table, register + login routes, JWT auth

**Stack decisions so far:**
- Python + FastAPI for backend (already knew Python)
- Neon.tech for PostgreSQL (Codespaces had permission issues with local postgres)
- GitHub Codespaces for development environment

---

### Session 2 — Feb 27 2026
**Built:** JWT auth, register, login, protected routes, .env secrets
**Learned:**
- Why passwords are hashed and how bcrypt works
- What a JWT token is and how to decode it
- How to protect routes with Depends()
- How to use .env to keep secrets out of GitHub
- How to read tracebacks to find the actual error line

**Stuck on:** .env not reloading without restarting uvicorn
**Next session:** GET /users/me, then start users-circles relationship (join a circle, list my circles)

---

### Session 3 — Mar 2 2026
**Built:** GET /users/me, POST /circles/{id}/join, GET /users/me/circles, GET /circles/{id}/members, POST /circles/join-by-code, protected GET /circles
**Learned:**
- What a junction table is and why many-to-many relationships need one (users ↔ circles)
- How SQL JOINs work — connecting two tables where IDs match
- That JOINs work both directions — get circles for a user, get users for a circle
- JWT tokens are never stored in the database — they're decoded on the fly using JWT_SECRET
- How to debug an empty response by checking the actual data in Neon directly
- The Flask `return {}, 404` pattern doesn't work in FastAPI — always use `raise HTTPException`
- Duplicate key errors need to be caught explicitly when a user tries to join a circle twice

**Stuck on:** GET /users/me/circles returning empty — traced it to testing with a different user than the one who had joined the circle
**Next session:** API is feature-complete. Consider building a frontend or mobile client to consume it.
