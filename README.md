# Bloc

A private real-time chat app for friend groups. Users create or join invite-only groups ("blocs"), chat in real time via WebSockets, and manage membership with role-based access control.

**Live:** [bloc-join-gather.vercel.app](https://bloc-join-gather.vercel.app)

---

## Architecture

```
React + TypeScript (Vercel)
        │
        │ REST + WebSocket
        ▼
FastAPI (Railway)
        │
        ├── PostgreSQL (Neon.tech)
        └── Sentry (error tracking)
```

The frontend is a React SPA deployed on Vercel. The backend is a FastAPI application deployed on Railway, connected to a managed PostgreSQL instance on Neon. All communication is over HTTPS/WSS. Environment variables are managed via Pydantic Settings with startup validation — the app fails fast if any required variable is missing.

---

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| Backend | Python + FastAPI | Async support, automatic OpenAPI docs, clean dependency injection |
| Database | PostgreSQL on Neon | Serverless, branching for test isolation, familiar SQL |
| Auth | JWT + bcrypt | Stateless tokens, industry-standard password hashing |
| Real-time | WebSockets (FastAPI) | Persistent connection, server-side broadcast to all room members |
| Migrations | Alembic | Version-controlled schema changes, reproducible across environments |
| Frontend | React + TypeScript | Type safety, component model fits the chat UI |
| Hosting | Railway + Vercel | Auto-deploy from GitHub, zero config |
| Observability | Sentry + structured logging | Error tracking, per-request latency and status code logging |
| Testing | pytest + httpx | TestClient hits real routes against an isolated test database |

---

## Key Technical Decisions

### Cursor-based pagination over offset
Message history uses a `before` cursor (message ID) instead of `LIMIT/OFFSET`. Offset pagination degrades as the table grows — fetching page 100 requires scanning and discarding 5000 rows. Cursor pagination is O(log n) with an index regardless of table size.

### JWT blocklist for server-side logout
JWTs are stateless by design — deleting a token from localStorage doesn't invalidate it on the server. On logout, the token's `jti` (JWT ID) is written to a `revoked_tokens` table. Every protected route checks this table before trusting the token. The table is indexed on `expires_at` for efficient cleanup of expired entries.

### Single JOIN query to eliminate N+1
The original `GET /users/me/circles` fetched member lists with a separate query per bloc — 1 + N database calls on every page load. `GET /users/me/circles/full` replaces this with a single four-table JOIN, collapsing flat rows into a nested structure in Python. For a user in 5 blocs, this goes from 6 queries to 1.

### Client-side message cache
Messages are cached in a module-level Map keyed by circle ID. On first app load, message history for all blocs is prefetched in the background. Navigating into a chat renders cached messages instantly while a fresh fetch runs silently. The cache is updated by incoming WebSocket messages to stay in sync.

### WebSocket membership check
WebSocket connections verify JWT validity and circle membership before `accept()` is called. A valid token alone is not sufficient — a user who has been kicked cannot reconnect to that room.

### Role-based access control
Membership is stored in a `user_circles` junction table with a `role` column (`admin` or `member`). Admin-only actions (kick, delete bloc, transfer admin) check this column before executing. Transferring admin is an atomic two-update transaction — the current admin is demoted and the target is promoted in the same commit. Admins cannot leave a bloc with other members without first transferring ownership.

### Connection leak prevention
Every database route wraps its connection in `try/finally: conn.close()`. Without this, an exception mid-route leaves a connection open. psycopg2 connections are not pooled — each request opens a new connection, so leaks accumulate until the server exhausts available connections.

---

## API Reference

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/users/register` | — | Create account |
| POST | `/users/login` | — | Login, returns JWT |
| POST | `/users/logout` | ✓ | Revoke token server-side |
| GET | `/users/me` | ✓ | Get current user |
| PATCH | `/users/me` | ✓ | Update username |
| GET | `/users/me/circles/full` | ✓ | All blocs with members (single query) |
| POST | `/circles` | ✓ | Create a bloc |
| POST | `/circles/join-by-code` | ✓ | Join by invite code |
| DELETE | `/circles/{id}/leave` | ✓ | Leave a bloc |
| GET | `/circles/{id}/members` | ✓ | List members with roles |
| DELETE | `/circles/{id}/members/{uid}` | ✓ Admin | Kick a member |
| PATCH | `/circles/{id}/transfer-admin` | ✓ Admin | Transfer admin ownership |
| DELETE | `/circles/{id}` | ✓ Admin | Delete bloc and all data |
| GET | `/circles/{id}/messages` | ✓ | Message history (cursor pagination) |
| WS | `/circles/{id}/ws` | ✓ | Real-time chat |

---

## Database Schema

```sql
users
  id, username, email, password_hash, created_at

circles
  id, name, invite_code, created_at

user_circles                          -- junction table
  user_id → users(id) ON DELETE CASCADE
  circle_id → circles(id) ON DELETE CASCADE
  role: 'admin' | 'member'
  joined_at

messages
  id, circle_id → circles(id) ON DELETE CASCADE
  user_id → users(id) ON DELETE CASCADE
  content, created_at

revoked_tokens                        -- JWT blocklist
  jti (PRIMARY KEY), revoked_at, expires_at

-- Indexes
idx_messages_circle_id
idx_messages_created_at
idx_user_circles_user_id
idx_user_circles_circle_id
idx_revoked_tokens_expires
```

---

## Testing

19 passing tests covering all core flows and negative cases. Tests run against a separate Neon database — production data is never touched. Each test run tears down and recreates all tables.

```bash
pytest tests/ -v
```

Negative cases covered: wrong password, duplicate join, join with invalid invite code, leave when not a member, non-admin attempting kick, non-admin attempting delete.

---

## Local Development

```bash
# Clone and set up
git clone https://github.com/your-username/bloc
cd bloc
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Run the backend
uvicorn main:app --reload

# Run tests
pytest tests/ -v
```

**`.env`**
```
DB_URL=your_neon_connection_string
JWT_SECRET=your_secret_key
ENVIRONMENT=development
SENTRY_DSN=your_sentry_dsn
```

**`.env.test`**
```
DB_URL=your_neon_test_connection_string
JWT_SECRET=test-secret-key
RATE_LIMIT=1000/minute
```

Swagger UI available at `http://localhost:8000/docs`.

---

## Observability

Every HTTP request is logged with method, path, status code, and latency:

```
INFO  request - method=GET path=/users/me/circles/full status=200 duration=23.4ms
WARNING  request - method=POST path=/users/login status=401 duration=11.2ms
ERROR  request - method=GET path=/circles/99/messages status=500 duration=8.1ms
```

4xx responses log as WARNING, 5xx as ERROR. Unhandled exceptions are captured by Sentry with full stack traces.

---

## Known Limitations

- WebSocket auth passes the JWT as a query parameter — visible in server logs. Mitigation: short-lived handshake tokens would solve this but add complexity.
- No connection pooling — each request opens a new psycopg2 connection. Under sustained load this would become a bottleneck. PgBouncer or SQLAlchemy's pool would be the fix.
- RLS (Row Level Security) is not enforced at the database level — access control is handled entirely at the application layer via route guards. The database user is `neondb_owner` which bypasses RLS policies.
- Single Railway instance — WebSocket connections are held in memory. A second instance would not share connection state. Redis pub/sub would be required for horizontal scaling.
