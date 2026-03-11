# Bloc (formerly CircleShift)

## What is this
A private social app for friend groups called "blocs" — users register, log in, create or join blocs via invite codes, and see who's in them.

## What I've built so far

### Backend (FastAPI)
- `GET /hello` — health check
- `GET /test-db` — confirms database connection
- `GET /circles` — list all circles (protected)
- `POST /circles` — create a circle (protected), auto-generates invite code
- `GET /circles/{id}` — get a single circle
- `GET /circles/{id}/members` — see who's in a circle (protected)
- `POST /circles/{id}/join` — join a circle by ID (protected)
- `POST /circles/join-by-code` — join a circle by invite code (protected)
- `POST /users/register` — create an account
- `POST /users/login` — login and get a JWT token
- `GET /users/me` — get your own profile (protected)
- `GET /users/me/circles` — list the circles you've joined (protected)

### Frontend (React + TypeScript)
- Login and Register screens
- My Blocs — lists joined blocs with member counts, skeleton loading state
- Create a Bloc — name input, auto-generates invite code on backend
- Join a Bloc — invite code input
- Bloc Detail — bloc name, colour badge, member list, invite code with copy button
- Bottom nav, dark UI, violet accent, glass-card styling
- Connected to real API — no more mocks

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
- Profile section — show username, email, option to update display name
- Leave a bloc — one backend route, one button on BlocDetail
- "You" badge on members list — compare logged-in user ID to member IDs

### Soon
- Real-time chat per bloc — messages table, WebSockets on backend, chat UI on frontend
- PWA manifest — lets users add Bloc to iPhone home screen

### Later
- Push notifications — pairs with chat
- Image uploads — profile pictures, media in chat (requires file storage like Cloudflare R2)
- Bloc admin controls — kick members, delete a bloc, transfer ownership

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
- Deployed FastAPI backend to Railway (live at https://web-production-e808f.up.railway.app)
- Deployed React frontend to Vercel (live at https://bloc-join-gather.vercel.app)
- Created `requirements.txt` and `Procfile` for Railway deployment
- Added CORS middleware to allow Vercel frontend to talk to Railway backend
- Created `src/lib/api.ts` — central API helper that attaches JWT token to every request
- Swapped mock `AuthContext.tsx` for real login/register API calls
- Swapped mock `BlocContext.tsx` for real API calls to `/users/me/circles` and `/circles/{id}/members`
- Added `vercel.json` to fix client-side routing on Vercel
- Fixed login route to return `user_id` and `username` alongside the token
- Fixed `/users/me/circles` and `/circles/{id}/members` to return arrays directly instead of wrapped objects

**Learned:**
- What CORS is — browsers block requests between different origins unless the backend explicitly allows it
- How to add CORS middleware in FastAPI
- How Railway and Vercel connect to GitHub and auto-deploy on push
- Why API routes should return arrays directly, not wrapped in `{"circles": [...]}` objects
- How JWT tokens are stored in localStorage and attached to protected requests via Authorization header
- What a PWA is — web apps can be added to iPhone home screen and work like native apps
- How to read Vercel build logs to find TypeScript errors
- How to use Swagger (/docs) to manually test protected API routes

**Stuck on:**
- Lovable locked to read-only (free tier limit) — exported code to GitHub and switched to Vercel for hosting
- requirements.txt had 80+ unnecessary Jupyter packages — replaced with clean minimal version
- CORS blocking frontend requests — fixed by adding CORSMiddleware to FastAPI
- Token not saving — caused by missing `async` on login handler in Login.tsx
- Blocs not showing — caused by routes returning wrapped objects instead of plain arrays

**Next session:**
1. Fix re-render so blocs appear instantly after login without needing refresh
2. Add create bloc screen on the frontend
3. Clean up console.log debug lines
4. Test full join flow with invite code end to end

---

### Session 6 — Mar 11 2026
**Built:**
- Fixed BlocContext to watch React `user` state instead of `localStorage` directly — blocs now load instantly after login
- Added skeleton loading cards to My Blocs so the screen doesn't flash empty while fetching
- Added Create a Bloc screen — name input, navigates to new bloc's detail screen on success
- Fixed `POST /circles` to auto-generate an 8-character invite code on the backend
- Fixed `POST /circles` to insert the creator into `user_circles` so the new bloc appears on their home screen
- Fixed `POST /circles/join-by-code` to accept invite code as a request body instead of a query parameter
- Added invite code display with one-tap copy button to Bloc Detail screen
- Tested full end-to-end flow: register → login → create bloc → share invite code → new user joins → both see each other as members

**Learned:**
- Why `localStorage.getItem()` in a useEffect dependency doesn't work — React only re-renders when state changes, not when localStorage changes
- What a skeleton loading state is and how `animate-pulse` works in Tailwind
- The difference between a FastAPI query parameter (`def route(param: str)`) and a request body (`def route(body: Model)`) — and why it matters when the frontend sends JSON
- Why creating a resource doesn't automatically link it to the creator — junction tables need to be updated manually
- That a working MVP is resume-ready — it doesn't need every feature to be worth showing

**Stuck on:**
- Build failed on Vercel — `export default` was missing from MyBlocs.tsx after a paste
- New bloc not appearing on home screen — traced to creator not being inserted into `user_circles`
- Join by invite code failing — backend was expecting a query param, frontend was sending a JSON body

**Next session:**
1. Add profile section — show username, email, option to update display name
2. Add leave a bloc button on Bloc Detail
3. Show "You" badge next to logged-in user on members list
