# CircleShift API

## What is this
One or two sentences. What are you building and why.

## What I've built so far
List the routes that actually work right now. Not what you plan to build — what works today.

## Tech stack
What you're using and one sentence on why each thing.

## What I learned building this
Be honest. What clicked, what confused you, what surprised you.

## How to run it locally
The exact commands someone would need. Pretend you're explaining it to yourself from yesterday.

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
