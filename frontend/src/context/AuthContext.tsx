/**
 * context/AuthContext.tsx — Global auth state.
 *
 * WHY CONTEXT OVER ZUSTAND/REDUX:
 *   Auth state is read in many places (header, protected routes, API calls)
 *   but written rarely (login, logout, token refresh). React Context is
 *   exactly the right tool for this pattern — no extra library needed.
 *
 * WHAT IT DOES:
 *   - Holds the current User object (null when logged out)
 *   - Exposes login/register/logout actions
 *   - On app load, attempts a token refresh from the httpOnly cookie
 *     so users who closed the tab stay logged in on return
 */

import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";
import * as authApi from "@/api/auth";
import { HttpError } from "@/api/client";
import type { LoginRequest, RegisterRequest, User } from "@/types";

interface AuthContextValue {
  user: User | null;
  isLoading: boolean;
  login: (data: LoginRequest) => Promise<void>;
  register: (data: RegisterRequest) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true); // true until initial refresh attempt completes

  // On mount: try refreshing the access token from the httpOnly cookie.
  // If it works, the user is still logged in. If not (401), they need to log in again.
  useEffect(() => {
    authApi
      .refreshToken()
      .then(() => authApi.getMe())
      .then(setUser)
      .catch((err: unknown) => {
        // 401 is expected for first-time visitors or expired sessions — not an error.
        if (err instanceof HttpError && err.status === 401) return;
        console.error("Token refresh failed:", err);
      })
      .finally(() => setIsLoading(false));
  }, []);

  const login = useCallback(async (data: LoginRequest) => {
    const me = await authApi.login(data);
    setUser(me);
  }, []);

  const register = useCallback(async (data: RegisterRequest) => {
    const me = await authApi.register(data);
    setUser(me);
  }, []);

  const logout = useCallback(async () => {
    await authApi.logout();
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, isLoading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

/** Hook — use auth state anywhere inside AuthProvider. */
export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}
