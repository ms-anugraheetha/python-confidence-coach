/**
 * LeftNav.tsx — Left navigation sidebar.
 *
 * Self-contained: reads the current route from useLocation to highlight
 * the active item, and navigates via useNavigate on click.
 * No active/onChange props needed — the URL is the source of truth.
 */

import clsx from "clsx";
import { useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";

type NavItem = "home" | "chat" | "progress" | "settings";

const ROUTE_MAP: Record<NavItem, string> = {
  home:     "/",
  chat:     "/coach",
  progress: "/progress",
  settings: "/settings",
};

function routeToNavItem(pathname: string): NavItem {
  if (pathname === "/coach")    return "chat";
  if (pathname === "/progress") return "progress";
  if (pathname === "/settings") return "settings";
  return "home";
}

function NavIcon({ item }: { item: NavItem }) {
  const cls = "h-4 w-4 flex-shrink-0";
  switch (item) {
    case "home":
      return (
        <svg className={cls} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>
        </svg>
      );
    case "chat":
      return (
        <svg className={cls} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/>
        </svg>
      );
    case "progress":
      return (
        <svg className={cls} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>
        </svg>
      );
    case "settings":
      return (
        <svg className={cls} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z"/>
        </svg>
      );
  }
}

const NAV_GROUPS: { label?: string; items: NavItem[] }[] = [
  {
    items: ["chat"],
  },
  {
    label: "Tracking",
    items: ["progress"],
  },
];

const NAV_LABELS: Record<NavItem, string> = {
  home:     "Home",
  chat:     "Chat Coach",
  progress: "Progress",
  settings: "Settings",
};

function NavButton({
  item,
  active,
  onClick,
}: {
  item: NavItem;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={clsx(
        "flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all duration-100",
        active
          ? "bg-[#111111] text-white"
          : "text-[#666666] hover:bg-[#F0F0F0] hover:text-[#111111]",
      )}
    >
      <NavIcon item={item} />
      <span>{NAV_LABELS[item]}</span>
    </button>
  );
}

export function LeftNav() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const { pathname } = useLocation();
  const active = routeToNavItem(pathname);

  const initials = user?.display_name
    ? user.display_name.slice(0, 2).toUpperCase()
    : "U";
  const displayName = user?.display_name ?? "User";

  return (
    <aside
      className="flex h-full w-nav flex-shrink-0 flex-col"
      style={{
        background: "#FFFFFF",
        borderRight: "1px solid #EAEAEA",
      }}
    >
      {/* Logo */}
      <div className="flex items-center gap-3 px-5 py-5">
        <div
          className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-xl"
          style={{ background: "#111111" }}
        >
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <circle cx="5" cy="8" r="3" fill="white" fillOpacity="0.9"/>
            <circle cx="11" cy="8" r="3" fill="white" fillOpacity="0.5"/>
          </svg>
        </div>
        <div>
          <p className="text-[13px] font-bold leading-tight text-[#111111]" style={{ letterSpacing: "-0.01em" }}>
            Python
          </p>
          <p className="text-[10px] font-medium text-[#999999]">
            Confidence Coach
          </p>
        </div>
      </div>

      {/* Nav groups */}
      <nav className="flex flex-1 flex-col gap-5 overflow-y-auto px-3 pb-4">
        {NAV_GROUPS.map((group, gi) => (
          <div key={gi}>
            {group.label && (
              <p className="mb-1 px-3 text-[10px] font-semibold uppercase tracking-[0.08em] text-[#BBBBBB]">
                {group.label}
              </p>
            )}
            <div className="flex flex-col gap-0.5">
              {group.items.map((item) => (
                <NavButton
                  key={item}
                  item={item}
                  active={active === item}
                  onClick={() => navigate(ROUTE_MAP[item])}
                />
              ))}
            </div>
          </div>
        ))}

        {/* Settings pinned at bottom */}
        <div className="mt-auto flex flex-col gap-0.5">
          <NavButton
            item="settings"
            active={active === "settings"}
            onClick={() => navigate(ROUTE_MAP.settings)}
          />
        </div>
      </nav>

      {/* Upgrade CTA */}
      <div className="mx-3 mb-3 rounded-2xl p-4" style={{ background: "#FAFAFA", border: "1px solid #EAEAEA" }}>
        <div className="mb-1 flex items-center gap-2">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#111" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
          </svg>
          <p className="text-[12px] font-semibold text-[#111111]">Go Premium</p>
        </div>
        <p className="mb-3 text-[11px] leading-relaxed text-[#999999]">
          Unlock advanced features, personalized learning and more!
        </p>
        <button
          className="w-full rounded-xl py-2 text-[12px] font-semibold text-white transition-all hover:opacity-90"
          style={{ background: "#111111" }}
        >
          Upgrade Now
        </button>
      </div>

      {/* User profile */}
      <div
        className="flex items-center gap-3 px-4 py-4"
        style={{ borderTop: "1px solid #EAEAEA" }}
      >
        <div
          className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full text-[11px] font-bold text-white"
          style={{ background: "#111111" }}
        >
          {initials}
        </div>
        <div className="flex-1 min-w-0">
          <p className="truncate text-[13px] font-semibold text-[#111111]">
            {displayName}
          </p>
          <p className="truncate text-[11px] text-[#999999]">
            {user?.email ?? ""}
          </p>
        </div>
        <button
          onClick={logout}
          title="Sign out"
          className="flex-shrink-0 rounded-lg p-1.5 text-[#BBBBBB] transition-colors hover:bg-[#F4F4F4] hover:text-[#666666]"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/>
          </svg>
        </button>
      </div>
    </aside>
  );
}
