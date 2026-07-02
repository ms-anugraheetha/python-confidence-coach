/**
 * components/chat/ConversationSidebar.tsx — Chat history sidebar.
 *
 * Shows all past conversations, highlights the active one, and
 * provides a "New chat" button at the top.
 */

import clsx from "clsx";
import type { Conversation } from "@/types";

interface ConversationSidebarProps {
  conversations: Conversation[];
  activeConversationId: string | null;
  isLoading: boolean;
  onSelect: (id: string) => void;
  onNew: () => void;
}

function formatRelativeTime(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60_000);
  const diffHours = Math.floor(diffMs / 3_600_000);
  const diffDays = Math.floor(diffMs / 86_400_000);

  if (diffMins < 1)   return "just now";
  if (diffMins < 60)  return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7)   return `${diffDays}d ago`;

  return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

function ConversationItem({
  conversation,
  active,
  onClick,
}: {
  conversation: Conversation;
  active: boolean;
  onClick: () => void;
}) {
  const title = conversation.title?.trim() || "New conversation";

  return (
    <button
      onClick={onClick}
      className={clsx(
        "flex w-full flex-col items-start gap-0.5 rounded-xl px-3 py-2.5 text-left transition-all duration-100",
        active
          ? "bg-[#111111] text-white"
          : "text-[#555555] hover:bg-[#F0F0F0] hover:text-[#111111]",
      )}
    >
      <span
        className="w-full truncate text-[12px] font-medium leading-snug"
        style={{ maxWidth: "100%" }}
      >
        {title}
      </span>
      <span
        className={clsx(
          "text-[10px] font-normal",
          active ? "text-[#888888]" : "text-[#BBBBBB]",
        )}
      >
        {formatRelativeTime(conversation.last_message_at || conversation.created_at)}
      </span>
    </button>
  );
}

export function ConversationSidebar({
  conversations,
  activeConversationId,
  isLoading,
  onSelect,
  onNew,
}: ConversationSidebarProps) {
  return (
    <aside
      className="flex h-full w-[200px] flex-shrink-0 flex-col"
      style={{
        background: "#FAFAFA",
        borderRight: "1px solid #EAEAEA",
      }}
    >
      {/* Header */}
      <div
        className="flex flex-shrink-0 items-center justify-between px-3 py-3"
        style={{ borderBottom: "1px solid #EAEAEA" }}
      >
        <span className="text-[11px] font-semibold uppercase tracking-[0.08em] text-[#BBBBBB]">
          Chats
        </span>
        <button
          onClick={onNew}
          title="New chat"
          className="flex h-6 w-6 items-center justify-center rounded-lg text-[#999999] transition-colors hover:bg-[#EAEAEA] hover:text-[#111111]"
        >
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
          </svg>
        </button>
      </div>

      {/* List */}
      <div className="flex flex-1 flex-col gap-0.5 overflow-y-auto px-2 py-2">
        {isLoading ? (
          <>
            {[80, 60, 72, 50].map((w, i) => (
              <div
                key={i}
                className="mx-1 mb-1 h-10 animate-pulse rounded-xl"
                style={{ background: "#EFEFEF", width: `${w}%` }}
              />
            ))}
          </>
        ) : conversations.length === 0 ? (
          <p className="px-3 pt-4 text-[11px] text-[#CCCCCC]">
            No chats yet.
          </p>
        ) : (
          conversations.map((convo) => (
            <ConversationItem
              key={convo.id}
              conversation={convo}
              active={convo.id === activeConversationId}
              onClick={() => onSelect(convo.id)}
            />
          ))
        )}
      </div>
    </aside>
  );
}
