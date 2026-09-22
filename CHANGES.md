# Changes Made to the Original ChatGPT-Generated Project

This document lists exactly what was changed from the originally uploaded
`ASKLY-Full-Project.zip`, and why. See `EXPLAIN_EVERYTHING.md` for the deep
explanation of how every part of the system works.

## Security fixes
- **Removed insecure default JWT secret** (`"change-me"`) — `JWT_SECRET` is now
  a required environment variable; the app refuses to start without it.
- **Added rate limiting** (`app/core/rate_limit.py`) on `/auth/login`,
  `/auth/register`, `/chat`, and `/quiz/generate` — prevents brute-force
  login attempts and API-cost abuse.
- **Enforced upload size limit** on PDF uploads (was defined in settings but
  never actually checked).
- **Same generic error message** for "wrong password" and "no such user" on
  login, to avoid leaking which emails are registered.
- **Fixed missing `email-validator` dependency** — `pydantic.EmailStr` needs
  this package; the app would crash on startup without it.

## Reliability / error-handling fixes
- Corrupt/unreadable PDF uploads now return a clean 400 error instead of
  crashing with a 500.
- Invalid MongoDB ObjectIds (malformed conversation/document IDs) now return
  400 instead of crashing.
- Web search (Tavily) failures now degrade gracefully to "no web results"
  instead of failing the entire chat request.
- LLM/quiz-generation failures return a generic client-safe error instead of
  leaking internal exception details.

## Readability / code quality
- Rewrote every backend file from single-line/minified style into normal,
  readable formatting with clear variable names.
- Replaced unexplained magic numbers (RRF's `60`, mastery's `0.7`/`0.3`,
  quiz difficulty thresholds) with named constants and comments explaining
  what they mean and why those specific values were chosen.
- Added docstrings explaining the *why* behind each non-obvious algorithm:
  hybrid retrieval + Reciprocal Rank Fusion, embedding normalization,
  exponential-moving-average mastery tracking, chunking with overlap.
- Cleaned up `frontend/lib/api.ts` and `frontend/components/Guard.tsx`
  (the two most-shared frontend files) with the same treatment; noted the
  localStorage-vs-httpOnly-cookie trade-off directly in a comment.

## Testing (there were zero tests before)
Added 26 tests across:
- `tests/unit/test_security.py` — password hashing, JWT create/verify, forged-token rejection
- `tests/unit/test_mastery.py` — EMA update logic, clamping, edge cases
- `tests/unit/test_document_chunking.py` — text splitting, overlap, empty input
- `tests/unit/test_retrieval.py` — hybrid RRF fusion, per-user data isolation
- `tests/unit/test_rate_limit.py` — limiter allows/blocks correctly
- `tests/integration/test_auth_flow.py` — full register → login → protected route flow, rate limiting

All 26 pass using an in-memory mocked MongoDB (`mongomock-motor`), so tests
run fast and don't need a real database connection.

## Not changed (still limitations - see EXPLAIN_EVERYTHING.md section 9)
- JWT still stored in frontend localStorage (not httpOnly cookies)
- Rate limiting is in-memory only (won't work across multiple server instances)
- Vector search is in-application, not a dedicated vector database
- No CI/CD, no structured logging/monitoring
