# Bloc — Dev Log

A session-by-session record of what was built, learned, and debugged.

---

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

---

### Session 15 — Apr 3 2026
**Built:** Alembic database migrations
- Installed Alembic and initialised it in the project root
- Configured `alembic/env.py` to pull `DB_URL` from Pydantic Settings (`settings.DB_URL`)
- Created a baseline migration capturing the full current schema
- Stamped the existing Neon database at head so Alembic knows the schema is already applied
- Verified the full upgrade/downgrade cycle works cleanly

**Learned:**
- How Alembic connects to the database via `env.py` and `alembic.ini`
- Why you stamp an existing database instead of running the baseline migration
- How `alembic upgrade head` and `alembic downgrade -1` work
- Never import from `app.config` if there's no `app` module — match your actual project structure
- Pydantic Settings preserves casing — `settings.DB_URL` not `settings.db_url`
- Every future schema change gets its own `alembic revision` file instead of raw SQL

---

### Session 16 — Apr 3 2026
**Built:** Transfer admin ownership + leave flow hardening
- New route `PATCH /circles/{id}/transfer-admin`
- Updated `DELETE /circles/{id}/leave` — blocks admin from leaving if other members exist
- Auto-delete bloc when last member leaves
- Added `TransferAdminRequest` Pydantic model to `models.py`

**Learned:**
- How to catch and surface backend error details on the frontend (`err?.detail`)
- Auto-delete is cleaner UX than leaving ghost blocs with no members
- Always initialise `conn` and `cursor` at the top of a route before any logic
- Route decorator prefix matters
- Sentry catches startup errors during the Railway deploy window
- Always `git pull` before `git push` in Codespaces to avoid rebase conflicts

**Stuck on:**
- Three separate Railway crash cycles — loose code outside function body, wrong import name, `bloc_logger` used directly instead of `logger`

---

### Session 17 — Apr 3 2026
**Built:** Transfer admin UI + leave flow update on frontend
- ShieldCheck icon next to each non-you member — visible to admin only
- `handleTransferAdmin` function with confirm dialog
- Updated `handleLeave` — client-side guard for admin with other members
- Tested full flow on live frontend

**Learned:**
- Client-side guards on destructive actions improve UX
- Surfacing `err?.detail` from the backend gives users the actual error
- A solo admin leaving is valid — auto-delete on backend handles it
- Two buttons in a member row need a flex container with a gap

---

### Session 18 — Apr 6 2026
**Built:** Frontend performance pass
- Silent refresh in BlocContext — navigating back to MyBlocs no longer shows skeletons
- Message prefetch cache (module-level Map in useChat) — chat opens instantly on repeat visits
- Chat.tsx pulls bloc name/member count from context instead of re-fetching
- BlocDetail.tsx pulls from context instead of re-fetching on mount
- Offline banner with 1s delay — prevents flash on initial WebSocket connect
- Send button spinner while message is in flight
- Input disabled with clear placeholder when WebSocket is down
- Fixed missing `websockets` package causing WebSocket connections to fail on Railway

**Learned:**
- Silent refresh pattern — update data in background without triggering loading state
- Module-level cache survives component unmount/remount within the same session
- Prefetching message history in BlocContext warms the cache before the user navigates in
- 1s delay on offline banner prevents false positives during normal WebSocket handshake

---

### Session 19 — Apr 6 2026
**Built:** Security audit
- Register returns 409 on duplicate email instead of 500
- Login returns identical 401 for bad email and wrong password — prevents account enumeration
- Connection leak audit — all routes now use try/finally: conn.close()
- WebSocket membership check before accept() — valid JWT alone is not sufficient
- Dead connection cleanup in ConnectionManager.broadcast
- Message length limit enforced on WebSocket path (was HTTP-only before)
- JWT blocklist on logout — jti written to revoked_tokens table, checked on every protected request
- Alembic migration for revoked_tokens table

**Learned:**
- psycopg2 error code 23505 = unique constraint violation
- Identical error responses for auth failures prevent enumeration attacks
- except HTTPException: raise is required inside bare except blocks to avoid swallowing intentional 403/404s
- JWT blocklist requires embedding a jti (uuid4) in the token payload at login time
- Circular import: router in auth.py caused import failure — moved logout route to users.py

---

### Session 20 — Apr 6 2026
**Built:** Systems and observability
- `GET /users/me/circles/full` — single four-table JOIN replaces 1+N query pattern
- BlocContext updated to use new endpoint — Promise.all member fetches eliminated
- BlocDetail updated to read from context instead of fetching on mount
- Request logging middleware — method, path, status code, latency on every request
- README rewritten — architecture diagram, technical decisions, API reference, known limitations
- Dev log moved to DEVLOG.md

**Learned:**
- Collapsing flat JOIN rows into nested structure in Python using a dict keyed by ID
- Middleware goes before routers to catch all requests including rate limit 429s
- Known limitations section signals engineering maturity — include what you haven't done and why

## Session 21 — May 5, 2026

### Focus
Production hardening + AI foundation (pgvector + Gemini embeddings)

### What was done

**Connection pooling**
Replaced per-request `psycopg2.connect()` with `ThreadedConnectionPool` (min=1, max=5).
Added `release_db()` to return connections to pool instead of closing them.
Updated all route handlers and `verify_token` to use `release_db`.

**WebSocket auth**
Removed JWT from query parameter (visible in server logs).
Implemented first-message auth: client connects, immediately sends
`{"type": "auth", "token": "..."}` as first frame. Server validates before
processing any messages. Added revoked token (jti) check to WebSocket path,
consistent with REST auth.

**pgvector setup**
Enabled vector extension on Neon via SQL editor — Alembic + PgBouncer pooler
connection silently drops DDL in transaction mode. Created `message_embeddings`
table (`vector(3072)`, ivfflat index) and `ai_logs` table. Added `DB_URL_DIRECT`
for Alembic-only use (direct connection, bypasses pooler).

**Gemini embedding service**
Installed `google-genai` SDK. Created `services/embeddings.py` using
`gemini-embedding-001` (3072 dimensions). Verified end to end: embedding
generated, stored in `message_embeddings`, latency logged to `ai_logs`.

**Production incident**
Railway `DB_URL` was pointing to wrong Neon database (`bloc_test` instead of
`neondb`). Fixed in Railway environment variables. Also removed
`channel_binding=require` which was causing psycopg2 connection failures.
Neon password was rotated mid-session — updated across `.env` and Railway.

### Issues encountered
- `CREATE EXTENSION vector` silently fails inside Alembic transaction on Neon
  pooler — solved by running manually in Neon SQL editor
- `gemini-embedding-001` produces 3072-dim vectors not 768 — updated table schema
- Pool exhaustion from bad connection validation fallback in `get_db()` — fixed
- Neon password rotation caused Railway auth failures — rotated and redeployed

### Current state
Production stable. All tables in place. Embedding service verified locally and
in production. Ready for Day 2 semantic search endpoint.

## Session 22 — May 6, 2026

### Focus
Semantic search endpoint — end to end

### What was done

**Bug fix: connection pool leak in users router**
Discovered `routers/users.py` was still calling `conn.close()` instead of
`release_db(conn)` across all routes (register, login, get_me, update_me,
get_my_circles, get_my_circles_full, logout). This was exhausting the
`ThreadedConnectionPool` on login, causing 500s. Fixed by importing
`release_db` and replacing all `conn.close()` calls.

**`search_messages()` in `services/embeddings.py`**
Added semantic search function that embeds the query string via
`generate_embedding()`, runs cosine similarity (`<=>`) against
`message_embeddings`, joins to `messages`, and returns results ranked by
similarity score (`1 - distance`). Fixed two bugs caught during testing:
- `embed_text` placeholder replaced with correct `generate_embedding`
- `m.sender_id` corrected to `m.user_id` to match actual schema

**`routers/ai.py`**
Created new router with `GET /circles/{circle_id}/search?q=` endpoint.
Includes membership check against `user_circles`, calls `search_messages()`,
returns ranked results with query echoed back. Fixed table name from
`circle_members` to `user_circles` during testing.

**Background embedding on message send**
Hooked `embed_message` into `routers/messages.py` in two places:
- REST route: via FastAPI `BackgroundTasks` — embedding fires after response
  is sent, sender doesn't wait on Gemini latency
- WebSocket route: via `asyncio.get_event_loop().run_in_executor()` —
  same effect inside the async WebSocket loop where `BackgroundTasks`
  is unavailable

**Registered router in `main.py`**
Added `ai_router` import and `app.include_router(ai_router)`.

### Issues encountered
- Pool exhaustion on login — `users.py` missed during Session 21 pooling
  migration, all routes still calling `conn.close()`
- `circle_members` table name in `ai.py` — correct name is `user_circles`
- `m.sender_id` column does not exist — correct column is `m.user_id`
- Push rejected twice due to remote divergence — resolved with
  `git pull --rebase origin main`

### Verification
End-to-end curl test passed in production:
- Sent two messages: "what time is the standup tomorrow" and
  "anyone free for lunch today"
- Searched "meeting schedule"
- Results correctly ranked by semantic similarity:
  - standup message → 0.82 (highest, no shared words with query)
  - lunch message → 0.78
  - "how's it going" (old message) → 0.76 (lowest, least relevant)

### Current state
Production stable. Semantic search live. Embeddings generated as background
tasks on every new message via both REST and WebSocket paths.

