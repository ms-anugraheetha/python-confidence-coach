import { useEffect, useRef } from "react";
import { MessageBubble } from "@/components/chat/MessageBubble";
import { ConfidenceCheckCard } from "@/components/chat/ConfidenceCheckCard";
import { TypingIndicator } from "@/components/chat/TypingIndicator";
import { MessageInput } from "@/components/chat/MessageInput";
import { Mascot } from "@/components/Mascot";
import type { ChatStatus, Message } from "@/types";

interface ChatPanelProps {
  userName?: string;
  messages: Message[];
  status: ChatStatus;
  error: string | null;
  onSend: (content: string) => void;
  onNewChat: () => void;
  onMessageReceived?: () => void;
}

const SUGGESTED_PROMPTS = [
  { icon: "</>", text: "Explain list comprehensions" },
  { icon: "⚙", text: "How do decorators work?" },
  { icon: "∿", text: "What is a generator?" },
  { icon: "👤", text: "Why do we use self in classes?" },
];

const TOPIC_CHIPS = [
  "Variables & Types", "Functions", "Loops", "Lists & Dicts",
  "Classes & OOP", "File I/O", "Exceptions", "Modules",
];

function HeroEmptyState({
  userName,
  onPrompt,
}: {
  userName: string;
  onPrompt: (p: string) => void;
}) {
  return (
    <div className="flex flex-1 flex-col overflow-y-auto">
      {/* Hero */}
      <div
        className="flex items-center justify-between px-8 pt-10 pb-8"
        style={{ borderBottom: "1px solid #EAEAEA" }}
      >
        <div>
          <h1
            className="text-[28px] font-bold text-[#111111]"
            style={{ letterSpacing: "-0.025em" }}
          >
            Hi, {userName}! 👋
          </h1>
          <p className="mt-1.5 text-[15px] text-[#666666]">
            Let's build your Python confidence today.
          </p>
        </div>
        <Mascot size={104} className="flex-shrink-0" />
      </div>

      {/* Ask Me Anything card */}
      <div className="px-8 pt-7">
        <div
          className="rounded-3xl p-6"
          style={{
            background: "#FFFFFF",
            border: "1px solid #EAEAEA",
            boxShadow: "0 4px 16px rgba(0,0,0,0.06), 0 1px 3px rgba(0,0,0,0.04)",
          }}
        >
          <h2
            className="mb-1 text-[17px] font-bold text-[#111111]"
            style={{ letterSpacing: "-0.015em" }}
          >
            Ask me anything
          </h2>
          <p className="mb-5 text-[13px] text-[#999999]">
            Paste code, describe an error, or ask about any Python concept.
          </p>

          <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 xl:grid-cols-4">
            {SUGGESTED_PROMPTS.map((p) => (
              <button
                key={p.text}
                onClick={() => onPrompt(p.text)}
                className="flex items-center gap-2.5 rounded-2xl px-4 py-3 text-left text-[12px] font-medium text-[#555555] transition-all duration-150 hover:border-[#D4D4D4] hover:bg-[#F7F7F7] hover:text-[#111111]"
                style={{
                  background: "#FAFAFA",
                  border: "1px solid #EAEAEA",
                }}
              >
                <span className="flex-shrink-0 font-mono text-[13px] text-[#999999]">{p.icon}</span>
                <span className="leading-snug">{p.text}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Topic chips */}
      <div className="px-8 pt-6 pb-8">
        <p className="mb-3 text-[11px] font-semibold uppercase tracking-[0.08em] text-[#BBBBBB]">
          Popular topics
        </p>
        <div className="flex flex-wrap gap-2">
          {TOPIC_CHIPS.map((topic) => (
            <button
              key={topic}
              onClick={() => onPrompt(`Explain ${topic} in Python`)}
              className="rounded-full px-3.5 py-1.5 text-[12px] font-medium text-[#666666] transition-all hover:border-[#111111] hover:bg-[#111111] hover:text-white"
              style={{
                background: "#FFFFFF",
                border: "1px solid #EAEAEA",
              }}
            >
              {topic}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

function renderMessage(msg: Message) {
  if (msg.role === "assistant" && msg.confidence_check) {
    return <ConfidenceCheckCard key={msg.id} message={msg} />;
  }
  return <MessageBubble key={msg.id} message={msg} />;
}

export function ChatPanel({
  userName = "there",
  messages,
  status,
  error,
  onSend,
  onNewChat,
  onMessageReceived,
}: ChatPanelProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, status]);

  const prevLengthRef = useRef(messages.length);
  useEffect(() => {
    const last = messages[messages.length - 1];
    if (messages.length > prevLengthRef.current && last?.role === "assistant") {
      onMessageReceived?.();
    }
    prevLengthRef.current = messages.length;
  }, [messages, onMessageReceived]);

  const hasMessages = messages.length > 0;

  return (
    <div className="flex h-full flex-col" style={{ background: "#FAFAFA" }}>

      {/* Chat header — shown when there are messages */}
      {hasMessages && (
        <div
          className="flex flex-shrink-0 items-center justify-between px-6 py-4"
          style={{ background: "#FFFFFF", borderBottom: "1px solid #EAEAEA" }}
        >
          <div className="flex items-center gap-2.5">
            <span
              className="text-[14px] font-semibold text-[#111111]"
              style={{ letterSpacing: "-0.01em" }}
            >
              Chat Coach
            </span>
            <span
              className="rounded-md px-1.5 py-0.5 text-[10px] font-semibold text-[#999999]"
              style={{ background: "#F4F4F4" }}
            >
              {messages.length}
            </span>
          </div>
          <button
            onClick={onNewChat}
            className="flex items-center gap-1.5 rounded-xl px-3 py-1.5 text-[12px] font-semibold text-[#666666] transition-all hover:bg-[#F4F4F4] hover:text-[#111111]"
            style={{ border: "1px solid #EAEAEA" }}
          >
            <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
            </svg>
            New chat
          </button>
        </div>
      )}

      {/* Messages / hero state */}
      <div className="flex flex-1 flex-col overflow-y-auto">
        {!hasMessages ? (
          <HeroEmptyState userName={userName} onPrompt={onSend} />
        ) : (
          <div className="flex flex-col gap-5 px-6 py-6">
            {messages.map(renderMessage)}
            {status === "sending" && <TypingIndicator />}
            {error && (
              <div
                className="rounded-2xl px-4 py-3 text-sm text-[#666666]"
                style={{
                  background: "#FFFFFF",
                  border: "1px solid #EAEAEA",
                  boxShadow: "0 1px 3px rgba(0,0,0,0.04)",
                }}
              >
                {error}
              </div>
            )}
            <div ref={bottomRef} />
          </div>
        )}
      </div>

      <MessageInput onSend={onSend} status={status} />
    </div>
  );
}
