/**
 * api/auth.ts — Auth endpoint functions.
 */

import { api, setToken, clearToken } from "@/api/client";
import type { User, AuthTokens, LoginRequest, RegisterRequest } from "@/types";

export async function googleLogin(credential: string): Promise<User> {
  const tokens = await api.post<AuthTokens>("/api/v1/auth/google", { credential });
  setToken(tokens.access_token);
  return api.get<User>("/api/v1/auth/me");
}

export async function login(data: LoginRequest): Promise<User> {
  // FastAPI OAuth2 expects form data for /token, but we use JSON here.
  // The backend /api/v1/auth/login route accepts JSON and returns tokens + user.
  const tokens = await api.post<AuthTokens>("/api/v1/auth/login", data);
  setToken(tokens.access_token);
  return api.get<User>("/api/v1/auth/me");
}

export async function register(data: RegisterRequest): Promise<User> {
  const tokens = await api.post<AuthTokens>("/api/v1/auth/register", data);
  setToken(tokens.access_token);
  return api.get<User>("/api/v1/auth/me");
}

export async function logout(): Promise<void> {
  try {
    await api.post<void>("/api/v1/auth/logout", {});
  } finally {
    clearToken();
  }
}

export async function refreshToken(): Promise<void> {
  // The httpOnly refresh-token cookie is sent automatically via credentials: 'include'.
  const tokens = await api.post<AuthTokens>("/api/v1/auth/refresh", {});
  setToken(tokens.access_token);
}

export async function getMe(): Promise<User> {
  return api.get<User>("/api/v1/auth/me");
}
