// Central place every page calls the backend through - keeps auth-token
// handling and error formatting consistent instead of repeating it in
// every page's fetch() calls.

export const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const TOKEN_KEY = "askly_token";

// An Error that also remembers the HTTP status code (401, 429, 500 ...), so
// callers can react differently to "not logged in" vs "server hiccup".
export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

export async function api(path: string, opts: RequestInit = {}) {
  // NOTE (security trade-off, worth knowing): the JWT is stored in
  // localStorage here for simplicity. That's readable by any JavaScript
  // running on the page, so it's vulnerable to XSS (if an attacker ever
  // got a script to run on this site, they could steal the token). The
  // more production-hardened alternative is an httpOnly cookie, which
  // JavaScript can't read at all - worth migrating to if this goes
  // fully to production.
  const token = typeof window !== "undefined" ? localStorage.getItem(TOKEN_KEY) : null;

  const headers = new Headers(opts.headers);
  if (!(opts.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API}${path}`, { ...opts, headers });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({ detail: response.statusText }));
    // FastAPI validation errors come back as a list; show something readable
    const detail = typeof errorBody.detail === "string" ? errorBody.detail : "Request failed";
    throw new ApiError(detail, response.status);
  }

  return response.json();
}

export function saveToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

export function hasToken(): boolean {
  return typeof window !== "undefined" && !!localStorage.getItem(TOKEN_KEY);
}