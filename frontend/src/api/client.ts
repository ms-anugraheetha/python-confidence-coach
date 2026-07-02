/**
 * api/client.ts — Typed fetch wrapper.
 *
 * WHY NOT AXIOS:
 *   fetch is built into every modern browser. One less dependency.
 *   This wrapper gives us the same convenience (base URL, auth headers,
 *   JSON serialisation, error extraction) without the bundle weight.
 *
 * USAGE:
 *   import { api } from '@/api/client'
 *   const data = await api.get<DashboardData>('/api/v1/dashboard')
 *   const msg  = await api.post<SendMessageResponse>('/api/v1/chat/message', body)
 *
 * AUTH:
 *   The access token is stored in memory (not localStorage) to mitigate XSS.
 *   The refresh token lives in an httpOnly cookie — the browser sends it
 *   automatically on /api/v1/auth/refresh calls.
 *   setToken() is called after login/register; clearToken() on logout.
 */

/** The error shape our FastAPI backend always returns. */
export interface ApiError {
  code: string;
  message: string;
  details: Record<string, unknown>;
}

/** Thrown when the server returns a non-2xx status. */
export class HttpError extends Error {
  constructor(
    public readonly status: number,
    public readonly error: ApiError,
  ) {
    super(error.message);
    this.name = "HttpError";
  }
}

// ── Token store (in-memory) ───────────────────────────────────────────────────

let _accessToken: string | null = null;

export function setToken(token: string): void {
  _accessToken = token;
}

export function clearToken(): void {
  _accessToken = null;
}

export function hasToken(): boolean {
  return _accessToken !== null;
}

// ── Core fetch wrapper ────────────────────────────────────────────────────────

async function request<T>(
  method: string,
  path: string,
  body?: unknown,
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    Accept: "application/json",
  };

  if (_accessToken) {
    headers["Authorization"] = `Bearer ${_accessToken}`;
  }

  const response = await fetch(path, {
    method,
    headers,
    credentials: "include", // sends the httpOnly refresh-token cookie
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (!response.ok) {
    let error: ApiError;
    try {
      error = (await response.json()) as ApiError;
    } catch {
      // Server returned non-JSON (e.g., 502 from proxy)
      error = {
        code: "NETWORK_ERROR",
        message: `HTTP ${response.status}: ${response.statusText}`,
        details: {},
      };
    }
    throw new HttpError(response.status, error);
  }

  // 204 No Content — return empty object
  if (response.status === 204) {
    return {} as T;
  }

  return response.json() as Promise<T>;
}

// ── Public API surface ────────────────────────────────────────────────────────

export const api = {
  get: <T>(path: string) => request<T>("GET", path),
  post: <T>(path: string, body: unknown) => request<T>("POST", path, body),
  put: <T>(path: string, body: unknown) => request<T>("PUT", path, body),
  patch: <T>(path: string, body: unknown) => request<T>("PATCH", path, body),
  delete: <T>(path: string) => request<T>("DELETE", path),
};
