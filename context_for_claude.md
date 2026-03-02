## Context for AI assistant
- Building: CircleShift API (private social app for friend groups)
- Language: Python + FastAPI
- Database: PostgreSQL on Neon.tech
- Environment: GitHub Codespaces
- Current file: main.py in /workspaces/circleshift-api
- Last working route: POST /circles/join-by-code (protected with JWT)

## Completed routes (all working)
- GET /hello
- GET /test-db
- GET /circles (protected)
- POST /circles (protected)
- GET /circles/{id}
- GET /circles/{id}/members (protected)
- POST /circles/{id}/join (protected)
- POST /circles/join-by-code (protected)
- POST /users/register
- POST /users/login
- GET /users/me (protected)
- GET /users/me/circles (protected)

## Database tables
- users (id, username, email, password_hash)
- circles (id, name, invite_code, created_at)
- user_circles (user_id, circle_id, joined_at) — junction table, PRIMARY KEY on both columns

## Auth
- JWT working, passwords hashed with bcrypt, secrets in .env
- verify_token() returns the full payload dict — access user id with user["user_id"]
- Tokens are never stored in the database — decoded on the fly using JWT_SECRET

## Known issues / things to watch
- login route still uses Flask-style `return {}, 404` instead of `raise HTTPException` — needs fixing
- join routes should wrap the INSERT in try/except to handle duplicate joins gracefully

## Status
- API is feature-complete for a usable v1
- Next logical step: build a frontend or mobile client to consume the API

## About the developer
- Beginner — explain things from first principles
- Learning by doing (vibecoding but wants to understand the code)
- Goal: build something end-to-end and usable, not just collect routes
