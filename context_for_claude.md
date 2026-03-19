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
- POST /circles (protected) — auto-generates 8-character invite code, adds creator to user_circles
- GET /circles/{id}
- GET /circles/{id}/members (protected) — returns array directly
- POST /circles/{id}/join (protected) — handles duplicate joins with try/except
- DELETE /circles/{id}/leave (protected) — removes user from user_circles
- POST /circles/join-by-code (protected) — accepts JSON body { invite_code }
- POST /users/register
- POST /users/login — returns { token, user_id, username }
- GET /users/me (protected)
- PATCH /users/me (protected) — updates username
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
- On page load, AuthContext calls GET /users/me to rehydrate user from token — no logout on refresh

## Deployment
- Backend: Railway (auto-deploys from circleshift-api GitHub repo)
- Frontend: Vercel (auto-deploys from bloc-join-gather GitHub repo)
- Database: Neon.tech (no change needed)
- Railway env vars: DB_URL, JWT_SECRET
- Procfile: web: uvicorn main:app --host 0.0.0.0 --port $PORT

## Frontend — React + TypeScript (bloc-join-gather repo)
- App is called Bloc
- Screens: Login/Register, My Blocs, Create a Bloc, Join a Bloc, Bloc Detail, Profile
- UI: dark theme, violet accent, glass-card styling, Space Grotesk + Inter fonts, bottom nav

## Key frontend files
- src/lib/api.ts — central API helper, reads token from localStorage, attaches as Bearer header
- src/context/AuthContext.tsx — login/register/logout, rehydrates user from token on page load, exposes setUser
- src/context/BlocContext.tsx — fetches real blocs from API, watches user state to trigger fetch
- src/pages/Login.tsx — async handleSubmit calling real login()
- src/pages/Register.tsx — async handleSubmit calling real register()
- src/pages/JoinBloc.tsx — async handleSubmit calling real joinBloc()
- src/pages/CreateBloc.tsx — name input, calls POST /circles, navigates to new bloc detail on success
- src/pages/BlocDetail.tsx — fetches bloc directly from API if not in local state, invite code copy button, leave button, You badge
- src/pages/MyBlocs.tsx — skeleton loading state, + button top right navigates to /create, refreshes on mount
- src/pages/Profile.tsx — shows username and email, edit username inline, logout button
- src/components/BottomNav.tsx — Blocs, Join, Profile tabs (logout moved to Profile screen)
- vercel.json — rewrites all routes to index.html for client-side routing

## Auth flow (working)
- On page load: AuthContext checks localStorage for token, calls GET /users/me to restore session
- login() calls POST /users/login, stores token in localStorage, sets user state
- register() calls POST /users/register, then calls login() automatically
- logout() clears token from localStorage, clears user state
- apiFetch() in api.ts reads token from localStorage and attaches to every request
- BlocContext watches user state from AuthContext — blocs fetch immediately when user logs in
- AuthContext exposes setUser so Profile screen can update username in state after saving

## Key patterns learned
- FastAPI query param: def route(param: str) — reads from URL ?param=value
- FastAPI request body: def route(body: Model) — reads from JSON body
- Always insert creator into junction table after creating a resource
- useEffect dependency must be React state, not localStorage directly
- Skeleton loading with animate-pulse prevents empty screen flash
- Rehydrate auth state on page load by calling /users/me with stored token
- Return null from AuthProvider while loading to prevent login screen flash on refresh
- Route ordering in React Router matters — catch-all path="*" must always be last

## Security fixes applied
- Removed GET /circles which exposed all circles to any logged-in user (data leak)
- POST /circles/{id}/join now handles duplicate joins with try/except and returns 400
- No rate limiting yet — known gap for future sessions

## Known issues / tech debt
- My Blocs calls refreshBlocs() on every mount — slightly inefficient but fine for MVP
- No database indexes yet — will slow down at scale
- No rate limiting on auth endpoints
- Railway cold starts cause ~7 second delay on first request after inactivity

## Next session goals
1. WhatsApp-style navigation — tap bloc in MyBlocs goes straight to /blocs/:id/chat
2. Chat header shows bloc name + member count, tappable to open BlocDetail (group info)
3. BlocDetail becomes group info screen — back arrow returns to chat, remove Open Chat button
4. Timestamps on messages in Chat
5. WebSocket auto-reconnect logic in useChat.ts
 
## Future features (post-MVP)
- Push notifications (pairs with chat)
- Image uploads for profile pictures (requires file storage like Cloudflare R2)
- Bloc admin controls — kick members, delete a bloc, transfer ownership
- Database indexes for performance
- Rate limiting on auth endpoints
- Capacitor wrapper for App Store submission
 
## About the developer
- Beginner — explain things from first principles
- Learning by doing (vibecoding but wants to understand the code)
- Goal: build something end-to-end and usable fast, eventually generate revenue
- Based in Canada
- App is resume-ready — full stack, real-time chat, PWA, deployed
