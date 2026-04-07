# Senior Engineering Code Review

Date: 2026-04-07
Scope: FastAPI backend (`main.py`, `routers/*`, `auth.py`, test coverage)

## Executive Summary

The codebase is readable and has solid fundamentals (parameterized SQL, password hashing, JWT revocation support, and clear route organization). The biggest risks are **authorization gaps** and one **debug endpoint exposed without auth**. Those are high-severity because they can lead to data leakage and unauthorized writes.

## Findings

### 1) Unauthenticated database introspection endpoint exposed in production (High)
- **Where**: `GET /test-db` in `main.py`.
- **Why this matters**: Any caller can retrieve active DB name + DB user, which is environment leakage and useful reconnaissance data.
- **Evidence**: Route has no auth dependency and directly returns DB metadata.
- **Recommendation**: Remove endpoint entirely or gate behind environment + admin auth, and ensure it is disabled in production.

### 2) Missing membership/authorization check on `POST /circles/{circle_id}/messages` (High)
- **Where**: `send_message` in `routers/messages.py`.
- **Why this matters**: Any authenticated user can post into any circle ID if they can guess or enumerate IDs. This breaks room isolation.
- **Evidence**: `send_message` validates content but does not validate membership before insert, unlike `get_messages` and websocket endpoint which do check membership.
- **Recommendation**: Add `SELECT 1 FROM user_circles ...` guard before insert and return `403` when not a member.

### 3) Member list leakage via `GET /circles/{circle_id}/members` (High)
- **Where**: `get_circle_members` in `routers/circles.py`.
- **Why this matters**: Endpoint requires a token but does not require requester membership in target circle. Any authenticated user can enumerate group composition.
- **Evidence**: Code checks only `circles.id` existence, then returns all members.
- **Recommendation**: Add membership authorization check (or admin-only policy depending on product requirements).

### 4) Circle metadata + invite code exposed via unauthenticated `GET /circles/{circle_id}` (Medium)
- **Where**: `get_circle` in `routers/circles.py`.
- **Why this matters**: Endpoint is public and returns invite code, enabling brute-force circle discovery and unauthorized joining attempts.
- **Recommendation**: Require auth and membership (or at minimum redact `invite_code` from this endpoint and restrict retrieval).

### 5) Over-broad exception handling can mask operational failures (Medium)
- **Where**: Multiple routes (`join_circle`, `join_by_code`, `create_circle`, etc.).
- **Why this matters**: Catch-all `except Exception` paths sometimes map different failure modes to the same status code, making incident triage difficult.
- **Recommendation**: Catch specific DB exceptions (e.g., unique violation) and log structured context including SQLSTATE when safe.

### 6) Test suite misses key authorization regressions (Medium)
- **Where**: `tests/test_api.py`.
- **Why this matters**: There are no negative tests for non-member posting messages or non-member listing members. Current gaps allowed issues #2 and #3 to persist.
- **Recommendation**: Add tests for:
  - non-member send message -> `403`
  - non-member list members -> `403`
  - anonymous access to circle details (if policy is private) -> expected denial/redaction

## Positive Notes

- Consistent parameterized SQL usage reduces injection risk.
- JWT revocation (`jti`) support is a good security pattern for logout.
- `users/me/circles/full` correctly addresses N+1 query behavior.
- Logging includes useful request latency and status metadata.

## Suggested Remediation Order

1. Remove/secure `/test-db`.
2. Add membership guard to message creation route.
3. Add authorization guard to members route.
4. Harden circle metadata exposure policy.
5. Improve exception typing + observability.
6. Expand authz-focused tests to prevent regressions.
