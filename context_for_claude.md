## Context for AI assistant
- Building: Bloc (formerly CircleShift) — a private social app for friend groups
- Language: Python + FastAPI (backend), React + TypeScript (frontend)
- Database: PostgreSQL on Neon.tech
- Environment: GitHub Codespaces (backend), GitHub editor (frontend)
- Backend repo: circleshift-api
- Frontend repo: bloc-join-gather

## Live URLs
- Backend: https://web-production-e808f.up.railway.app
- Frontend: https://bloc-join-gather.vercel.app

## Backend — completed routes (all working)
- GET /hello
- GET /test-db
- POST /circles (protected) — auto-generates 8-character invite code, adds creator to user_circles
- GET /circles/{id}
- GET /circles/{id}/members (protected) — returns array directly
- POST /circles/{id}/join (protected) — handles duplicate joins with try/except
- DELETE /circles/{id}/leave (protected) — removes user from user_circles
- POST /circles/join-by-code (protected) — accepts JSON body { invite_code }
- POST /users/register — rate limited 5/minute
- POST /users/login — returns { token, user_id, username }, rate limited 5/minute
- GET /users/me (protected)
- PATCH /users/me (protected) — updates username
- GET /users/me/circles (protected) — returns array directly
- GET /circles/{id}/messages (protected) — returns message history, ordered by created_at ASC
- POST /circles/{id}/messages (protected) — saves a message (HTTP fallback, main path is WebSocket)
- WebSocket /circles/{circle_id}/ws — real-time chat, JWT auth via query param, broadcasts to all circle members

## File structure
- main.py — app setup, middleware, router registration, /hello and /test-db
- auth.py — get_db(), verify_token(), DB_URL, JWT_SECRET
- models.py — all Pydantic models with Field validation
- routers/users.py — all /users routes
- routers/circles.py — all /circles routes
- routers/messages.py — messages + WebSocket + ConnectionManager
- conftest.py — pytest fixtures, test DB setup, rate limit disabled via RATE_LIMIT env var
- tests/test_api.py — 13 passing tests

## Database tables
- users (id, username, email, password_hash)
- circles (id, name, invite_code, created_at)
- user_circles (user_id, circle_id, joined_at) — junction table, PRIMARY KEY on both columns
- messages (id, circle_id, user_id, content, created_at) — stored in UTC

## Auth
- JWT working, passwords hashed with bcrypt, secrets in .env
- verify_token() returns the full payload dict — access user id with user["user_id"]
- Tokens are never stored in the database — decoded on the fly using JWT_SECRET
- JWT tokens expire after 7 days — exp claim set on login
- CORS middleware added — only allows https://bloc-join-gather.vercel.app
- On page load, AuthContext calls GET /users/me to rehydrate user from token — no logout on refresh
- WebSocket auth — JWT passed as query param (?token=), verified before connection accepted, closes with code 1008 if invalid

## Deployment
- Backend: Railway (auto-deploys from circleshift-api GitHub repo)
- Frontend: Vercel (auto-deploys from bloc-join-gather GitHub repo)
- Database: Neon.tech (no change needed)
- Railway env vars: DB_URL, JWT_SECRET, SENTRY_DSN, ENVIRONMENT=production
- Procfile: web: uvicorn main:app --host 0.0.0.0 --port $PORT

## Frontend — React + TypeScript (bloc-join-gather repo)
- App is called Bloc
- Screens: Login/Register, My Blocs, Create a Bloc, Join a Bloc, Chat, Group Info (BlocDetail), Profile
- UI: dark theme, violet accent, glass-card styling, Space Grotesk + Inter fonts, bottom nav

## Navigation flow (WhatsApp-style)
- MyBlocs → tap bloc → /blocs/:id/chat (Chat screen)
- Chat header (bloc name + member count) → tap → /blocs/:id/info (Group Info screen)
- Group Info back arrow → /blocs/:id/chat
- Chat back arrow → / (MyBlocs)

## Key frontend files
- src/lib/api.ts — central API helper, reads token from localStorage, attaches as Bearer header
- src/context/AuthContext.tsx — login/register/logout, rehydrates user from token on page load, exposes setUser
- src/context/BlocContext.tsx — fetches real blocs from API, watches user state to trigger fetch
- src/pages/Login.tsx — async handleSubmit calling real login()
- src/pages/Register.tsx — async handleSubmit calling real register()
- src/pages/JoinBloc.tsx — async handleSubmit calling real joinBloc()
- src/pages/CreateBloc.tsx — name input, calls POST /circles, navigates to new bloc detail on success
- src/pages/BlocDetail.tsx — group info screen, fetches bloc + members, invite code copy, leave button, You badge, back arrow → chat
- src/pages/MyBlocs.tsx — skeleton loading state, + button top right navigates to /create, refreshes on mount, tapping bloc goes to chat
- src/pages/Chat.tsx — real-time chat, fetches bloc name + member count for header, tappable header → group info, timestamps on messages, auto-scroll
- src/pages/Profile.tsx — shows username and email, edit username inline, logout button
- src/hooks/useChat.ts — WebSocket hook, auto-reconnect on disconnect (3s delay), shouldReconnect ref prevents reconnect after unmount
- src/components/BottomNav.tsx — Blocs, Join, Profile tabs
- vercel.json — rewrites all routes to index.html for client-side routing

## App.tsx routes
- / → MyBlocs
- /join → JoinBloc
- /blocs/:id → BlocDetail (legacy, still works)
- /blocs/:id/info → BlocDetail (group info, back arrow → chat)
- /blocs/:id/chat → Chat
- /create → CreateBloc
- /profile → Profile

## Auth flow (working)
- On page load: AuthContext checks localStorage for token, calls GET /users/me to restore session
- login() calls POST /users/login, stores token in localStorage, sets user state
- register() calls POST /users/register, then calls login() automatically
- logout() clears token from localStorage, clears user state
- apiFetch() in api.ts reads token from localStorage and attaches to every request
- BlocContext watches user state from AuthContext — blocs fetch immediately when user logs in
- AuthContext exposes setUser so Profile screen can update username in state after saving

## Testing (all passing)
- Test runner: pytest with httpx and FastAPI TestClient
- Test database: separate Neon database (bloc_test) — never touches prod data
- Config: .env.test loaded in conftest.py with override=True before app imports
- Rate limiting disabled in tests via RATE_LIMIT=1000/minute in .env.test
- conftest.py: session-scoped client and db fixtures, autouse clean_db fixture wipes tables after every test in foreign key safe order (messages → user_circles → circles → users)
- 13 tests covering: register, login, wrong password, get_me, no token, create circle, creator auto-added as member, join by ID, duplicate join, join by invite code, invalid invite code, leave circle, leave when not a member

## Input validation (Pydantic Field)
- username: min 2, max 30 characters
- email: max 100 characters
- password: min 6, max 72 characters
- bloc name: min 1, max 50 characters
- invite code: max 20 characters
- message content: max 1000 characters (enforced in route)

## Security fixes applied
- Removed GET /circles which exposed all circles to any logged-in user (data leak)
- POST /circles/{id}/join handles duplicate joins with try/except and returns 400
- WebSocket auth — token verified before connection accepted, closes with 1008 if invalid
- JWT tokens expire after 7 days
- Rate limiting on /users/login and /users/register — 5 requests per minute per IP via slowapi
- Input validation on all models — max lengths enforced by Pydantic Field() before route code runs

## Error tracking
- Sentry installed on backend — captures unhandled exceptions with full stack traces
- Environment-aware — development vs production set via ENVIRONMENT env var
- traces_sample_rate=0.2 — 20% of requests tracked for performance

## Known issues / tech debt
- My Blocs calls refreshBlocs() on every mount — slightly inefficient but fine for MVP
- No database indexes yet — planned for Session 12
- Railway cold starts cause ~7 second delay on first request after inactivity
- WebSocket ConnectionManager holds connections in memory — won't work across multiple Railway instances, needs Redis pub/sub at scale

## Key patterns learned
- FastAPI query param: def route(param: str) — reads from URL ?param=value
- FastAPI request body: def route(body: Model) — reads from JSON body
- Always insert creator into junction table after creating a resource
- useEffect dependency must be React state, not localStorage directly
- Skeleton loading with animate-pulse prevents empty screen flash
- Rehydrate auth state on page load by calling /users/me with stored token
- Return null from AuthProvider while loading to prevent login screen flash on refresh
- Route ordering in React Router matters — catch-all path="*" must always be last
- Timestamps from backend are UTC strings — append Z if missing so browser interprets correctly
- WebSocket auto-reconnect: extract connect() into useCallback, use shouldReconnect ref to prevent reconnect after unmount
- pytest fixtures: scope="session" creates once for all tests, autouse=True runs automatically
- Test the negative cases — verifies error handling works
- @limiter.limit() captures the limiter reference at import time — can't swap the object after the fact
- Use env vars to change behaviour between test and production (e.g. RATE_LIMIT)
- FastAPI routers: APIRouter() replaces @app, included in main.py with include_router()
- Auth and models in separate files — routers import from them without circular dependencies

## Session roadmap
- Session 12 — Database and performance: indexes, pagination on messages and circles, EXPLAIN ANALYZE
- Session 13 — Observability and DevX: structured logging, Pydantic settings, proper README
- Session 14 — Bloc admin controls: kick members, delete bloc, role column in user_circles, tests written alongside feature
- Session 15 — PWA and App Store: Capacitor wrapper, push notifications groundwork, TestFlight

## Future features (post-MVP)
- Push notifications (pairs with chat)
- Image uploads for profile pictures (requires file storage like Cloudflare R2)
- Bloc admin controls — kick members, delete a bloc, transfer ownership
- Redis pub/sub for multi-instance WebSocket support
- Capacitor wrapper for App Store submission

## About the developer
- Beginner — explain things from first principles
- Learning by doing (vibecoding but wants to understand the code)
- Goal: build something end-to-end and usable fast, eventually generate revenue
- Based in Canada (Toronto)
- App is resume-ready — full stack, real-time chat, PWA, deployed, tested
- Workflow: edit frontend on GitHub editor (auto-deploys to Vercel), run backend in Codespace (git pull to sync, then pytest/uvicorn)
- Always provide commit messages with code changes
