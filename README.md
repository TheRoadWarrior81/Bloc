# Bloc (formerly CircleShift)

## What is this
A private social app for friend groups called "blocs" — users register, log in, create or join blocs via invite codes, and see who's in them.

## What I've built so far

### Backend (FastAPI)
- `POST /circles` — create a circle (protected), auto-generates invite code, adds creator to user_circles
- `GET /circles/{id}` — get a single circle
- `GET /circles/{id}/members` — see who's in a circle (protected)
- `POST /circles/{id}/join` — join a circle by ID (protected), handles duplicate joins
- `DELETE /circles/{id}/leave` — leave a circle (protected)
- `POST /circles/join-by-code` — join a circle by invite code (protected)
- `POST /users/register` — create an account
- `POST /users/login` — login and get a JWT token
- `GET /users/me` — get your own profile (protected)
- `PATCH /users/me` — update username (protected)
- `GET /users/me/circles` — list the circles you've joined (protected)

### Frontend (React + TypeScript)
- Login and Register screens
- My Blocs — lists joined blocs with member counts, skeleton loading state
- Create a Bloc — name input, auto-generates invite code on backend
- Join a Bloc — invite code input
- Bloc Detail — bloc name, colour badge, member list, invite code with copy button, leave button, You badge
- Profile — view username and email, edit username, logout
- Bottom nav with Blocs, Join, Profile tabs
- Session persistence — stay logged in after page refresh
- Dark UI, violet accent, glass-card styling

## Tech stack
- **Python + FastAPI** — already knew Python, FastAPI is fast to get routes working
- **PostgreSQL on Neon.tech** — Codespaces had permission issues with local postgres, Neon just works
- **GitHub Codespaces** — dev environment in the browser, no local setup
- **JWT + bcrypt** — industry standard auth, passwords hashed, tokens stateless
- **psycopg2** — connects Python to PostgreSQL
- **React + TypeScript via Lovable** — AI-generated frontend, dark UI, mobile-friendly
- **Railway** — backend hosting, auto-deploys from GitHub
- **Vercel** — frontend hosting, auto-deploys from GitHub

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
- What a data leak is and how dead backend routes can expose data unintentionally

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

## Roadmap

### Next session
- PWA manifest — lets users add Bloc to iPhone home screen (no backend work needed)
- Start real-time chat — messages table, WebSocket route, chat UI

### Later
- Push notifications (pairs with chat)
- Image uploads for profile pictures (requires Cloudflare R2 or similar)
- Bloc admin controls — kick members, delete a bloc, transfer ownership
- Database indexes for performance at scale
- Rate limiting on auth endpoints

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
- Removed GET /circles data leak — route exposed all circles to any logged-in user
- Fixed POST /circles/{id}/join duplicate join handling with try/except
- Fixed session persistence — AuthContext now calls GET /users/me on page load to rehydrate user from stored token, no more logout on refresh
- Moved logout from bottom nav to Profile screen (standard UX pattern)
- Added Profile tab to bottom nav

**Learned:**
- How to rehydrate auth state on page load using a stored JWT — call /users/me with the token on mount
- Why returning null from AuthProvider during the loading check prevents the login screen from flashing on refresh
- What a data leak is — a route that returns data the logged-in user shouldn't have access to
- How PATCH works in FastAPI for partial updates
- Why DELETE /circles/{id}/leave uses rowcount to check if the user was actually in the circle
- Route ordering matters in React Router — catch-all path="*" must be last or it swallows valid routes

**Stuck on:**
- Vercel deployment stuck at initializing — fixed by redeploying from dashboard
- Hard refresh required after deploy due to browser cache

**Next session:**
1. PWA manifest — add to iPhone home screen
2. Start real-time chat feature
