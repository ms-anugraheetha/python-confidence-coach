/**
 * pages/SettingsPage.tsx — Account settings.
 *
 * Shows profile information and account actions.
 * Display name and email are read-only for now (no update endpoint yet).
 */

import { useNavigate } from "react-router-dom";
import { LeftNav } from "@/components/LeftNav";
import { useAuth } from "@/context/AuthContext";

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="mb-1.5 text-[11px] font-semibold uppercase tracking-[0.08em] text-[#BBBBBB]">
        {label}
      </p>
      <div
        className="w-full rounded-xl px-4 py-3 text-[13px] text-[#666666]"
        style={{ background: "#F4F4F4", border: "1px solid #EAEAEA" }}
      >
        {value}
      </div>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div
      className="rounded-2xl p-6"
      style={{ background: "#FFFFFF", border: "1px solid #EAEAEA", boxShadow: "0 1px 3px rgba(0,0,0,0.06)" }}
    >
      <h2 className="mb-4 text-[13px] font-semibold text-[#111111]">{title}</h2>
      {children}
    </div>
  );
}

export function SettingsPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const initials = user?.display_name
    ? user.display_name.slice(0, 2).toUpperCase()
    : "U";

  const joinedDate = user?.created_at
    ? new Date(user.created_at).toLocaleDateString("en-US", {
        month: "long",
        day: "numeric",
        year: "numeric",
      })
    : "—";

  async function handleLogout() {
    await logout();
    navigate("/login", { replace: true });
  }

  return (
    <div className="flex h-screen overflow-hidden" style={{ background: "#FAFAFA" }}>

      {/* Left nav (desktop) */}
      <div className="hidden lg:flex">
        <LeftNav />
      </div>

      {/* Main content */}
      <div className="flex flex-1 flex-col overflow-hidden">

        {/* Mobile top bar */}
        <div
          className="flex flex-shrink-0 items-center px-5 py-3.5 lg:hidden"
          style={{ background: "#FFFFFF", borderBottom: "1px solid #EAEAEA" }}
        >
          <div className="flex items-center gap-2.5">
            <div
              className="flex h-7 w-7 items-center justify-center rounded-lg"
              style={{ background: "#111111" }}
            >
              <svg width="13" height="13" viewBox="0 0 16 16" fill="none">
                <circle cx="5" cy="8" r="3" fill="white" fillOpacity="0.9"/>
                <circle cx="11" cy="8" r="3" fill="white" fillOpacity="0.5"/>
              </svg>
            </div>
            <span className="text-[13px] font-bold text-[#111111]">Settings</span>
          </div>
        </div>

        {/* Scrollable content */}
        <div className="flex-1 overflow-y-auto px-6 py-8 lg:px-10">
          <div className="mx-auto max-w-xl">

            {/* Header */}
            <div className="mb-8">
              <h1
                className="text-[24px] font-bold text-[#111111]"
                style={{ letterSpacing: "-0.02em" }}
              >
                Settings
              </h1>
              <p className="mt-1 text-[14px] text-[#999999]">
                Manage your account and preferences.
              </p>
            </div>

            <div className="flex flex-col gap-4">

              {/* Profile */}
              <Section title="Profile">
                {/* Avatar */}
                <div className="mb-5 flex items-center gap-4">
                  <div
                    className="flex h-14 w-14 flex-shrink-0 items-center justify-center rounded-full text-[16px] font-bold text-white"
                    style={{ background: "#111111" }}
                  >
                    {initials}
                  </div>
                  <div>
                    <p className="text-[14px] font-semibold text-[#111111]">
                      {user?.display_name ?? "User"}
                    </p>
                    <p className="text-[12px] text-[#999999]">Joined {joinedDate}</p>
                  </div>
                </div>

                <div className="flex flex-col gap-3">
                  <Field label="Display Name" value={user?.display_name ?? ""} />
                  <Field label="Email" value={user?.email ?? ""} />
                </div>
              </Section>

              {/* About */}
              <Section title="About">
                <div className="flex flex-col gap-3 text-[13px] text-[#666666]">
                  <div className="flex items-center justify-between">
                    <span>App</span>
                    <span className="font-medium text-[#111111]">Python Confidence Coach</span>
                  </div>
                  <div
                    className="flex items-center justify-between"
                    style={{ borderTop: "1px solid #F0F0F0", paddingTop: "12px" }}
                  >
                    <span>Version</span>
                    <span className="font-medium text-[#111111]">0.1.0</span>
                  </div>
                </div>
              </Section>

              {/* Danger zone */}
              <Section title="Account">
                <p className="mb-4 text-[12px] text-[#999999]">
                  Sign out of your account on this device.
                </p>
                <button
                  onClick={handleLogout}
                  className="flex items-center gap-2 rounded-xl px-4 py-2.5 text-[13px] font-semibold transition-all hover:opacity-80"
                  style={{ background: "#111111", color: "#FFFFFF" }}
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/>
                  </svg>
                  Sign Out
                </button>
              </Section>

            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
