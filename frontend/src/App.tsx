/**
 * App.tsx — Root component with routing.
 *
 * ROUTES:
 *   /          → HomePage    (dashboard overview)
 *   /coach     → CoachPage   (chat + progress sidebar)
 *   /progress  → ProgressPage
 *   /settings  → SettingsPage
 *   /login     → LoginPage
 *   /register  → RegisterPage
 *
 * PROTECTED ROUTES:
 *   <RequireAuth> wraps all app pages. Unauthenticated users are sent to /login.
 *   While the initial token refresh is in flight (isLoading=true), we show
 *   nothing to avoid a flash of the login page.
 */

import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { LoginPage } from "@/pages/LoginPage";
import { RegisterPage } from "@/pages/RegisterPage";
import { HomePage } from "@/pages/HomePage";
import { CoachPage } from "@/pages/CoachPage";
import { ProgressPage } from "@/pages/ProgressPage";
import { SettingsPage } from "@/pages/SettingsPage";

function RequireAuth({ children }: { children: React.ReactNode }) {
  const { user, isLoading } = useAuth();

  // Still attempting token refresh from cookie — don't redirect yet
  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center" style={{ background: "#FAFAFA" }}>
        <span className="animate-pulse-soft text-[13px] font-medium text-[#BBBBBB]">Loading…</span>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}

export function App() {
  return (
    <Routes>
      {/* Public */}
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      {/* Protected */}
      <Route path="/" element={<RequireAuth><HomePage /></RequireAuth>} />
      <Route path="/coach" element={<RequireAuth><CoachPage /></RequireAuth>} />
      <Route path="/progress" element={<RequireAuth><ProgressPage /></RequireAuth>} />
      <Route path="/settings" element={<RequireAuth><SettingsPage /></RequireAuth>} />

      {/* Fallback */}
      <Route path="*" element={<Navigate to="/coach" replace />} />
    </Routes>
  );
}
