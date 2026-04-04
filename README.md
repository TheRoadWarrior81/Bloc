# Bloc

## What is this
A private social app for friend groups called "blocs" — users register, log in, create or join blocs via invite codes, and chat in real time.

## What I've built so far

### Backend (FastAPI)
- `POST /circles` — create a bloc (protected), auto-generates invite code, adds creator as admin
- `GET /circles/{id}` — get a single bloc
- `GET /circles/{id}/members` — see who's in a bloc with their roles (protected)
- `POST /circles/{id}/join` — join a bloc by ID (protected), handles duplicate joins
- `DELETE /circles/{id}/leave` — leave a bloc (protected)
- `POST /circles/join-by-code` — join a bloc by invite code (protected)
- `DELETE /circles/{id}/members/{user_id}` — kick a member, admin only (protected)
- `DELETE /circles/{id}` — delete a bloc, admin only, cascades to all data (protected)
- `POST /users/register` — create an account
- `POST /users/login` — login and get a JWT token (expires in 7 days)
- `GET /users/me` — get your own profile (protected)
- `PATCH /users/me` — update username (protected)
- `GET /users/me/circles` — list the blocs you've joined (protected)
- `GET /circles/{id}/messages` — fetch message history with cursor-based pagination (protected)
- `WebSocket /circles/{id}/ws` — real-time chat, JWT verified on connect

### Frontend (React + TypeScript)
- Login and Register screens
- My Blocs — lists joined blocs, tap goes directly to chat (WhatsApp-style)
- Chat — real-time messaging, bloc name + member count in header, timestamps on messages, auto-reconnect on disconnect
- Group Info — tap chat header to see bloc details, members with roles, invite code, leave button, kick members (admin only), delete bloc (admin only)
- Create a Bloc — name input, auto-generates invite code on backend
- Join a Bloc — invite code input
- Profile — view username and email, edit username, logout
- Bottom nav with Blocs, Join, Profile tabs
- Session persistence — stay logged in after page refresh
- Dark UI, violet accent, glass-card styling

### Testing
- 19 passing tests covering all core API flows
- Separate test database on Neon — prod data never touched
- Clean teardown after every test — no state leaks between runs
- Covers: register, login, wrong password, no token, create bloc, creator auto-added as admin, join by ID, duplicate join, join by invite code, invalid invite code, leave, leave when not a member, creator is admin, member role, kick member, non-admin cannot kick, delete bloc, non-admin cannot delete

## Tech stack
- **Python + FastAPI** — already knew Python, FastAPI is fast to get routes working
- **PostgreSQL on Neon.tech** — Codespaces had permission issues with local postgres, Neon just works
- **GitHub Codespaces** — dev environment in the browser, no local setup
- **JWT + bcrypt** — industry standard auth, passwords hashed, tokens stateless
- **psycopg2** — connects Python to PostgreSQL
- **WebSockets** — real-time chat via FastAPI WebSocket support
- **slowapi** — rate limiting on auth endpoints
- **Pydantic Settings** — centralized env var management with validation
- **pytest + httpx** — backend test suite, TestClient hits real routes against a test DB
- **React + TypeScript via Lovable** — AI-generated frontend, dark UI, mobile-friendly
- **Railway** — backend hosting, auto-deploys from GitHub
- **Vercel** — frontend hosting, auto-deploys from GitHub
- **Sentry** — error tracking on backend, captures unhandled exceptions
- **Structured logging** — timestamped log lines across all routers via bloc_logger.py

## Live URLs
- **Backend:** https://web-production-e808f.up.railway.app
- **Frontend:** https://bloc-join-gather.vercel.app

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
- How to debug an empty API response by checking the database directly
- The difference between Figma, Lovable, v0 and when to use each
- What Firebase is and why building manually teaches you more
- How to deploy a FastAPI backend to Railway
- How to deploy a React frontend to Vercel
- What CORS is and why the backend needs to allow the frontend's origin
- Why API routes should return arrays directly, not wrapped in objects
- How JWT tokens are stored in localStorage and attached to protected requests
- What a PWA is and how a web app can be added to iPhone home screen
- Why React useEffect dependencies matter — localStorage is not reactive, state is
- How skeleton loading states improve perceived performance
- Why the creator of a resource needs to be added to junction tables manually
- The difference between query parameters and request body in FastAPI
- How to rehydrate auth state on page load using a stored JWT token
- Why returning null from a provider during loading prevents screen flashes
- How route ordering in React Router works — catch-all must always be last
- How WebSockets work — persistent connection, broadcast to all members in a room
- Why WebSocket auth uses a query param instead of a header
- How auto-reconnect works — useCallback + a ref flag to prevent reconnecting after unmount
- Why UTC timestamps need a Z suffix so browsers parse them correctly
- What pytest fixtures are and how scope and autouse work
- Why you need a separate test database — tests must never touch prod data
- How to test negative cases — wrong password, duplicate join, leaving when not a member
- What `git pull` does and why you run it before starting work in a Codespace
- What database indexes are and how EXPLAIN ANALYZE shows whether they're being used
- How cursor-based pagination works — fetch DESC, reverse, use before param for older messages
- Why Pydantic Settings validates env vars at startup instead of failing later
- Never name a file logger.py or log.py — conflicts with Python built-ins
- How ON DELETE CASCADE works and how to add it to an existing FK constraint
- How role-based access control works — store a role column, check it before destructive actions
- Why database migrations should always happen before pushing new code

## How to run it locally
```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn main:app --reload

# Run tests
pytest tests/ -v
```

Then open `/docs` in your browser to test routes via Swagger UI.

Make sure your `.env` file has:
```
DB_URL=your_neon_connection_string
JWT_SECRET=your_secret_key
ENVIRONMENT=development
SENTRY_DSN=your_sentry_dsn
```

And `.env.test` for running the test suite:
```
DB_URL=your_neon_test_database_connection_string
JWT_SECRET=test-secret-key
RATE_LIMIT=1000/minute
```

## Roadmap

### Next session (15)
- Capacitor wrapper for App Store / TestFlight submission
- Push notifications groundwork

### Later
- Transfer admin ownership when admin leaves a bloc
- Push notifications (pairs with chat)
- Image uploads for profile pictures (requires Cloudflare R2 or similar)
- Redis pub/sub for multi-instance WebSocket support

---

## Dev Log

### Session 1 — Feb 20 2026
**Built:** GET /circles, POST /circles, connected to Neon PostgreSQL
**Learned:**
- How a FastAPI route connects to a database
- Why POST needs conn.commit() but GET doesn't
- What RETURNING does in a SQL INSERT

**Stuck on:** PostgreSQL sudo permissions in Codespaces (solved by using Neon instead)
**Next session:** Build users table, register + login routes, JWT auth

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
**Next session:** GET /users/me, then start users-circles relationship

---

### Session 3 — Mar 2 2026
**Built:** GET /users/me, POST /circles/{id}/join, GET /users/me/circles, GET /circles/{id}/members, POST /circles/join-by-code, protected GET /circles
**Learned:**
- What a junction table is and why many-to-many relationships need one
- How SQL JOINs work — connecting two tables where IDs match
- JOINs work both directions — get circles for a user, get users for a circle
- JWT tokens are never stored in the database
- How to debug an empty response by checking Neon directly
- Flask-style `return {}, 404` doesn't work in FastAPI — use `raise HTTPException`

**Stuck on:** GET /users/me/circles returning empty — traced to testing with wrong user
**Next session:** Deploy to Railway, connect Lovable frontend to real API

---

### Session 4 — Mar 6 2026
**Built:** Lovable frontend — Login, Register, My Blocs, Join a Bloc, Bloc Detail screens
**Decided:**
- Renamed app from CircleShift to Bloc
- Chose Lovable over v0/Bolt for speed
- Chose Railway over AWS for deployment (simpler, free tier, no overkill)
- Frontend is mocked via React context, ready to wire to real API

**Learned:**
- Difference between Figma (design tool) and Lovable (AI code generator)
- Difference between Lovable, v0, and Bolt — and when to use each
- What Firebase is and how it compares to building your own backend
- JWT tokens live in the frontend after login — need to store and attach to every protected request

**Next session:** Deploy FastAPI to Railway, swap Lovable mocks for real API calls

---

### Session 5 — Mar 7 2026
**Built:**
- Deployed FastAPI backend to Railway
- Deployed React frontend to Vercel
- Created requirements.txt and Procfile for Railway
- Added CORS middleware
- Created src/lib/api.ts — central API helper
- Swapped mock AuthContext and BlocContext for real API calls
- Added vercel.json for client-side routing
- Fixed login route to return user_id and username
- Fixed routes to return arrays directly

**Learned:**
- What CORS is and how to add CORSMiddleware in FastAPI
- How Railway and Vercel auto-deploy from GitHub
- How JWT tokens are stored in localStorage and attached to requests
- How to read Vercel build logs to find TypeScript errors

**Stuck on:**
- Lovable locked to read-only — exported code to GitHub
- requirements.txt had 80+ unnecessary packages
- CORS blocking frontend requests
- Token not saving — missing async on login handler
- Blocs not showing — routes returning wrapped objects

**Next session:** Fix re-render, add create bloc screen, clean up debug lines

---

### Session 6 — Mar 11 2026
**Built:**
- Fixed BlocContext to watch React user state instead of localStorage
- Added skeleton loading cards to My Blocs
- Added Create a Bloc screen
- Fixed POST /circles to auto-generate invite code and insert creator into user_circles
- Fixed POST /circles/join-by-code to accept JSON body
- Added invite code display with copy button to Bloc Detail
- Tested full end-to-end flow

**Learned:**
- Why localStorage in useEffect dependency doesn't work
- What animate-pulse skeleton loading is
- Difference between FastAPI query param and request body
- Why junction tables need manual creator insertion

**Stuck on:**
- Missing export default on MyBlocs.tsx caused Vercel build failure
- Creator not inserted into user_circles
- Join by invite code — backend expected query param, frontend sent JSON body

**Next session:** Profile section, leave a bloc, You badge, security fixes

---

### Session 7 — Mar 13 2026
**Built:**
- Profile screen — view username and email, edit username, logout button
- PATCH /users/me backend route to update username
- Leave Bloc button on BlocDetail — calls DELETE /circles/{id}/leave
- DELETE /circles/{id}/leave backend route
- "You" badge next to logged-in user on members list
- Removed GET /circles data leak
- Fixed POST /circles/{id}/join duplicate join handling with try/except
- Fixed session persistence — AuthContext now rehydrates user from stored token on page load
- Moved logout from bottom nav to Profile screen

**Learned:**
- How to rehydrate auth state on page load using a stored JWT
- Why returning null from AuthProvider during loading prevents login screen flash
- What a data leak is
- How PATCH works in FastAPI for partial updates
- Why DELETE /circles/{id}/leave uses rowcount to check membership
- Route ordering matters in React Router

**Stuck on:**
- Vercel deployment stuck at initializing — fixed by redeploying from dashboard
- Hard refresh required after deploy due to browser cache

---

### Session 8 — Mar 15 2026
**Built:** PWA manifest + icons, real-time chat (WebSocket, messages table, chat UI)
**Learned:**
- How PWA manifest and apple meta tags work
- How WebSockets work in FastAPI with ConnectionManager
- Why uvicorn needs the websockets package installed
- How to pin a fixed input bar above bottom nav on mobile
- Why user ID comparisons need String() casting

**Stuck on:**
- Railway dropping WebSocket connections — fixed by adding websockets to requirements.txt
- Chat input hidden behind bottom nav on mobile — fixed with fixed positioning
- /bloc vs /blocs route mismatch broke navigation

---

### Session 9 — Mar 19 2026
**Built:**
- WhatsApp-style navigation — tapping a bloc in MyBlocs goes directly to chat
- Chat header shows bloc name + member count, tappable to open group info
- BlocDetail converted to group info screen — back arrow returns to chat, Open Chat button removed
- Added /blocs/:id/info route in App.tsx
- Timestamps on messages — shows local time (HH:MM) for today, date for older
- Fixed UTC timestamp parsing — appending Z so browser treats created_at as UTC correctly
- WebSocket auto-reconnect in useChat.ts — 3 second delay, stops reconnecting on unmount

**Learned:**
- How to extract a function into useCallback so it can safely call itself recursively
- Why a ref (shouldReconnect) is the right tool to control reconnect behaviour across renders
- UTC timestamps need Z suffix — without it browsers parse inconsistently
- Same component (BlocDetail) can serve two routes (/blocs/:id and /blocs/:id/info)

**Stuck on:** Nothing major this session

---

### Session 10 — Mar 20 2026
**Built:**
- Test database on Neon (bloc_test) — completely separate from prod
- .env.test config file for test environment
- conftest.py — pytest fixtures for client, db connection, and autouse table cleanup
- tests/test_api.py — 13 passing tests covering all core flows

**Learned:**
- What pytest fixtures are — scope="session" vs per-test, autouse=True
- Why test databases exist — never run tests against prod data
- How TestClient works — hits real FastAPI routes in memory, no server needed
- Why negative tests matter — wrong password, duplicate join, leaving when not a member
- Delete order matters with foreign keys — messages → user_circles → circles → users
- git pull syncs Codespace with GitHub before starting work
- Always activate venv before running Python commands

**Stuck on:** Nothing — clean session

---

### Session 11 — Mar 23 2026
**Built:**
- Rate limiting on /users/login and /users/register (5/minute via slowapi)
- Input validation on all Pydantic models using Field min/max lengths
- Refactored main.py into routers/users.py, routers/circles.py, routers/messages.py, auth.py, and models.py
- Sentry error tracking on backend

**Learned:**
- How slowapi rate limiting works
- How Pydantic Field() validates input before route code runs
- How FastAPI routers work
- What Sentry does

**Stuck on:**
- Rate limiter not disabled by app.state.limiter.enabled = False
- Codespace timeout mid-session

---

### Session 12 — Mar 28 2026
**Built:**
- 5 database indexes on messages, user_circles, and circles tables
- EXPLAIN ANALYZE before/after — confirmed query plan improvement (0.920ms → 0.028ms)
- Cursor-based pagination on GET /circles/{id}/messages — limit + before params, default 50
- Membership check added to GET /circles/{id}/messages (403 if not a member)

**Learned:**
- EXPLAIN ANALYZE shows whether PostgreSQL uses Seq Scan or Index Scan
- PostgreSQL skips indexes on tiny tables — kicks in automatically at scale
- Cursor-based pagination uses a before ID instead of page numbers
- Fetch DESC + reverse = get the N most recent in chronological order

**Stuck on:** Nothing — clean session

---

### Session 13 — Mar 28 2026
**Built:**
- config.py with Pydantic Settings — centralizes all env var reads with type validation
- bloc_logger.py — structured logging with timestamps and log levels
- Removed all os.getenv() calls from auth.py, main.py, and all routers
- Log lines on login, register, circle create/join/leave/kick/delete, WebSocket events

**Learned:**
- Pydantic Settings validates env vars at startup — fails fast if anything is missing
- Never name a file logger.py or log.py — conflicts with Python built-ins, causes circular imports
- Structured log format: timestamp, level, module name, message with key=value pairs

**Stuck on:**
- bloc_logger.py got corrupted with mixed file content during editing — replaced it clean

---

### Session 14 — Mar 28 2026
**Built:**
- role column on user_circles — admin or member, defaults to member
- Creator auto-assigned admin role on bloc creation
- GET /circles/{id}/members now returns role field
- DELETE /circles/{id}/members/{user_id} — kick route, admin only
- DELETE /circles/{id} — delete bloc route, admin only, cascades cleanly
- Fixed user_circles FK to ON DELETE CASCADE so circle deletion works
- Admin badge, kick buttons, delete button on Group Info screen — all conditional on role
- 6 new tests — 19 total, all passing

**Learned:**
- ON DELETE CASCADE must be on the FK constraint itself — DROP and re-ADD to change it
- Admin checks are just a role column lookup before the destructive action
- fetchBloc extracted from useEffect so kick handler can refresh members list
- Always do database migrations before pushing code to avoid Sentry errors during deploy window

**Stuck on:**
- test_admin_can_delete_circle failed — missing ON DELETE CASCADE on user_circles FK
- Sentry caught two real errors during deploy window (column not found, FK violation) — both resolved

### Session 15 — Apr 4 2026
**Built:** Alembic database migrations
- Installed Alembic and initialised it in the project root
- Configured `alembic/env.py` to pull `DB_URL` from Pydantic Settings (`settings.DB_URL`)
- Created a baseline migration capturing the full current schema — users, circles, user_circles, messages tables with all FK constraints and ON DELETE CASCADE rules
- Stamped the existing Neon database at head so Alembic knows the schema is already applied
- Verified the full upgrade/downgrade cycle works cleanly

**Learned:**
- How Alembic connects to the database via `env.py` and `alembic.ini`
- Why you stamp an existing database instead of running the baseline migration — the tables already exist
- How `alembic upgrade head` and `alembic downgrade -1` work
- Never import from `app.config` if there's no `app` module — match your actual project structure
- Pydantic Settings preserves casing — `settings.DB_URL` not `settings.db_url`
- Every future schema change gets its own `alembic revision` file instead of raw SQL

---

### Session 16 — Apr 4 2026
**Built:** Transfer admin ownership + leave flow hardening
- New route `PATCH /circles/{id}/transfer-admin` — admin only, demotes current admin to member, promotes target to admin, validates target is actually a member
- Updated `DELETE /circles/{id}/leave` — blocks admin from leaving if other members exist, returns 400 with clear error message
- Auto-delete bloc when last member leaves — after the membership row is deleted, checks remaining count and deletes the circle if zero, cascades cleanly to all related data
- Added `TransferAdminRequest` Pydantic model to `models.py`

**Learned:**
- How to catch and surface backend error details on the frontend (`err?.detail`)
- Auto-delete is cleaner UX than leaving ghost blocs with no members
- Always initialise `conn` and `cursor` at the top of a route before any logic — placing DB calls outside a function causes a `NameError` at import time and crashes the entire app on startup
- Route decorator prefix matters — `@router.patch("/{id}/transfer-admin")` won't match if all other routes use `/circles/{id}/...`
- `bloc_logger` is not a global — always use the local `logger` variable initialised with `get_logger()`
- Sentry catches startup errors during the Railway deploy window — useful for catching migration/code mismatch bugs before they become silent failures
- Always `git pull` before `git push` in Codespaces to avoid rebase conflicts

**Stuck on:**
- Three separate Railway crash cycles — loose code outside function body, wrong import name (`get_current_user` vs `verify_token`), `bloc_logger` used directly instead of `logger`
- Each crash caught via Railway logs and Sentry, fixed and redeployed

---

### Session 17 — Apr 4 2026
**Built:** Transfer admin UI + leave flow update on frontend
- Added `ShieldCheck` icon (violet) next to each non-you member in Group Info — visible to admin only
- `handleTransferAdmin` function — calls `PATCH /circles/{id}/transfer-admin`, refreshes member list on success, confirm dialog before executing
- Updated `handleLeave` — client-side check before hitting the backend: if user is admin and other members exist, show alert "You must transfer admin to another member before leaving" and return early
- Both transfer and kick buttons sit in a flex row next to each member row — shield on the left, kick on the right
- Tested full flow on live frontend: transfer works, leave blocked correctly for admin with members, leave succeeds for members and solo admins

**Learned:**
- Client-side guards on destructive actions improve UX — no need to wait for a 400 from the server to show a meaningful message
- Surfacing `err?.detail` from the backend gives users the actual error instead of a generic fallback
- A solo admin leaving is valid and correct — the auto-delete on the backend handles it cleanly
- Two buttons in a member row need a flex container with a gap — `ml-auto` on the container, not on individual buttons
