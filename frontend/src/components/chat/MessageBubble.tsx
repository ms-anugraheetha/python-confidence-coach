import clsx from "clsx";
import type { Message } from "@/types";
import { MascotAvatar } from "@/components/Mascot";

interface MessageBubbleProps {
  message: Message;
}

function renderContent(content: string): React.ReactNode {
  const parts = content.split(/(```[\s\S]*?```)/g);
  return parts.map((part, i) => {
    if (part.startsWith("```")) {
      const firstLine = part.split("\n")[0].replace("```", "").trim();
      const code = part.replace(/^```[^\n]*\n?/, "").replace(/```$/, "");
      return (
        <div key={i} className="my-3 overflow-hidden rounded-2xl" style={{ border: "1px solid #EAEAEA" }}>
          {firstLine && (
            <div
              className="flex items-center justify-between px-4 py-2"
              style={{ background: "#F4F4F4", borderBottom: "1px solid #EAEAEA" }}
            >
              <span className="font-mono text-[11px] font-medium text-[#999999]">{firstLine}</span>
              <button
                onClick={() => navigator.clipboard.writeText(code)}
                className="flex items-center gap-1 rounded-md px-2 py-0.5 text-[10px] font-medium text-[#999999] transition-all hover:bg-[#EAEAEA] hover:text-[#666666]"
              >
                <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/>
                </svg>
                Copy
              </button>
            </div>
          )}
          <pre
            className="overflow-x-auto p-4 text-[12px] font-mono leading-relaxed"
            style={{ background: "#FAFAFA", color: "#333333" }}
          >
            <code>{code}</code>
          </pre>
        </div>
      );
    }
    const inlineParts = part.split(/(`[^`]+`)/g);
    return (
      <span key={i}>
        {inlineParts.map((inline, j) => {
          if (inline.startsWith("`") && inline.endsWith("`")) {
            return (
              <code
                key={j}
                className="rounded-md px-1.5 py-0.5 font-mono text-[12px] text-[#333333]"
                style={{ background: "#F0F0F0", border: "1px solid #E4E4E4" }}
              >
                {inline.slice(1, -1)}
              </code>
            );
          }
          return inline.split("\n").map((line, k, arr) => (
            <span key={k}>
              {line}
              {k < arr.length - 1 && <br />}
            </span>
          ));
        })}
      </span>
    );
  });
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <div className={clsx("flex w-full animate-slide-up gap-3", isUser ? "flex-row-reverse" : "flex-row")}>

      {/* Avatar */}
      {isUser ? (
        <div
          className="mt-0.5 flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-full text-[10px] font-bold text-white"
          style={{ background: "#111111" }}
        >
          U
        </div>
      ) : (
        <div className="mt-0.5 flex-shrink-0">
          <MascotAvatar size={28} />
        </div>
      )}

      <div
        className={clsx(
          "max-w-[80%] text-sm leading-relaxed",
          isUser ? "rounded-3xl rounded-tr-md" : "rounded-3xl rounded-tl-md",
        )}
        style={
          isUser
            ? {
                background: "#FFFFFF",
                border: "1px solid #EAEAEA",
                color: "#111111",
                padding: "12px 16px",
                boxShadow: "0 1px 3px rgba(0,0,0,0.06)",
              }
            : {
                background: "#FFFFFF",
                border: "1px solid #EAEAEA",
                color: "#333333",
                padding: "14px 16px",
                boxShadow: "0 2px 8px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)",
              }
        }
      >
        {/* Topic badge */}
        {!isUser && message.topic_detected && (
          <span
            className="mb-2.5 inline-block rounded-full px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-[0.07em] text-[#999999]"
            style={{ background: "#F4F4F4", border: "1px solid #EAEAEA" }}
          >
            {message.topic_detected}
          </span>
        )}
        <div>{renderContent(message.content)}</div>

        {/* AI action buttons */}
        {!isUser && (
          <div className="mt-3 flex flex-wrap gap-2 pt-3" style={{ borderTop: "1px solid #F0F0F0" }}>
            {[
              { icon: "↩", label: "Explain more" },
              { icon: "</>", label: "Show example" },
              { icon: "?", label: "Give me a quiz" },
            ].map((action) => (
              <button
                key={action.label}
                className="flex items-center gap-1.5 rounded-xl px-3 py-1.5 text-[11px] font-medium text-[#888888] transition-all hover:bg-[#F4F4F4] hover:text-[#333333]"
                style={{ border: "1px solid #EAEAEA" }}
              >
                <span className="font-mono text-[10px]">{action.icon}</span>
                {action.label}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
