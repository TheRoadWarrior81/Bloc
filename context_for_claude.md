## Context for AI assistant
- Building: Bloc (formerly CircleShift) — a private social app for friend groups
- Language: Python + FastAPI (backend), React + TypeScript (frontend)
- Database: PostgreSQL on Neon.tech
- Environment: GitHub Codespaces (backend), GitHub (frontend)
- Backend repo: circleshift-api
- Frontend repo: bloc-join-gather

## Live URLs
- Backend: https://web-production-e808f.up.railway.app
- Frontend: https://bloc-join-gather.vercel.app

## Backend — completed routes (all working)
- GET /hello
- GET /test-db
- GET /circles (protected)
- POST /circles (protected)
- GET /circles/{id}
- GET /circles/{id}/members (protected) — returns array directly
- POST /circles/{id}/join (protected)
- POST /circles/join-by-code (protected)
- POST /users/register
- POST /users/login — returns { token, user_id, username }
- GET /users/me (protected)
- GET /users/me/circles (protected) — returns array directly

## Database tables
- users (id, username, email, password_hash)
- circles (id, name, invite_code, created_at)
- user_circles (user_id, circle_id, joined_at) — junction table, PRIMARY KEY on both columns

## Auth
- JWT working, passwords hashed with bcrypt, secrets in .env
- verify_token() returns the full payload dict — access user id with user["user_id"]
- Tokens are never stored in the database — decoded on the fly using JWT_SECRET
- CORS middleware added — only allows https://bloc-join-gather.vercel.app

## Deployment
- Backend: Railway (auto-deploys from circleshift-api GitHub repo)
- Frontend: Vercel (auto-deploys from bloc-join-gather GitHub repo)
- Database: Neon.tech (no change needed)
- Railway env vars: DB_URL, JWT_SECRET
- Procfile: web: uvicorn main:app --host 0.0.0.0 --port $PORT

## Frontend — React + TypeScript (bloc-join-gather repo)
- App is called Bloc
- Screens: Login/Register, My Blocs, Join a Bloc (invite code), Bloc Detail (members list)
- UI: dark theme, violet accent, glass-card styling, Space Grotesk + Inter fonts, bottom nav

## Key frontend files
- src/lib/api.ts — central API helper, reads token from localStorage, attaches as Bearer header
- src/context/AuthContext.tsx — real login/register/logout, stores JWT in localStorage
- src/context/BlocContext.tsx — fetches real blocs from API, handles join by invite code
- src/pages/Login.tsx — async handleSubmit calling real login()
- src/pages/JoinBloc.tsx — async handleSubmit calling real joinBloc()
- vercel.json — rewrites all routes to index.html for client-side routing

## Auth flow (working)
- login() calls POST /users/login, stores token in localStorage, sets user state
- register() calls POST /users/register, then calls login() automatically
- logout() clears token from localStorage, clears user state
- apiFetch() in api.ts reads token from localStorage and attaches to every request

## Known issues to fix
- Blocs don't appear instantly after login — need re-render trigger after token is saved
- POST /circles/{id}/join does not handle duplicate joins (no try/except)
- console.log debug lines still in AuthContext.tsx and BlocContext.tsx — remove before shipping
- login route still uses Flask-style error handling in one place

## Next session goals
1. Fix re-render so blocs appear instantly after login without refresh
2. Add create bloc screen on the frontend
3. Remove console.log debug lines
4. Test full join flow with invite code end to end

## Future features (post-MVP)
- Real-time chat per bloc (requires WebSockets + messages table)
- PWA manifest so users can add to iPhone home screen

## About the developer
- Beginner — explain things from first principles
- Learning by doing (vibecoding but wants to understand the code)
- Goal: build something end-to-end and usable fast
