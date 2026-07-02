import { useCallback, useRef, useState } from "react";
import type { ChatStatus } from "@/types";

interface MessageInputProps {
  onSend: (content: string) => void;
  status: ChatStatus;
  placeholder?: string;
}

export function MessageInput({
  onSend,
  status,
  placeholder = "Ask about any Python concept, paste code, or describe an error…",
}: MessageInputProps) {
  const [value, setValue] = useState("");
  const [focused, setFocused] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const isBusy = status !== "idle";
  const hasContent = value.trim().length > 0;

  const handleSubmit = useCallback(() => {
    const trimmed = value.trim();
    if (!trimmed || isBusy) return;
    onSend(trimmed);
    setValue("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  }, [value, isBusy, onSend]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setValue(e.target.value);
    const el = e.target;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 144)}px`;
  };

  return (
    <div
      className="flex-shrink-0 px-6 py-4"
      style={{ background: "#FFFFFF", borderTop: "1px solid #EAEAEA" }}
    >
      <div
        className="flex items-end gap-3 rounded-2xl px-4 py-3.5 transition-all duration-150"
        style={{
          background: "#FAFAFA",
          border: `1px solid ${focused ? "#D4D4D4" : "#EAEAEA"}`,
          boxShadow: focused ? "0 0 0 3px rgba(0,0,0,0.04)" : "none",
        }}
      >
        {/* Attachment & code buttons */}
        <div className="flex gap-1.5 mb-0.5">
          <button
            className="rounded-lg p-1.5 text-[#BBBBBB] transition-colors hover:bg-[#EAEAEA] hover:text-[#666666]"
            title="Attach file"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21.44 11.05l-9.19 9.19a6 6 0 01-8.49-8.49l9.19-9.19a4 4 0 015.66 5.66l-9.2 9.19a2 2 0 01-2.83-2.83l8.49-8.48"/>
            </svg>
          </button>
          <button
            className="rounded-lg p-1.5 text-[#BBBBBB] transition-colors hover:bg-[#EAEAEA] hover:text-[#666666]"
            title="Insert code"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/>
            </svg>
          </button>
        </div>

        <textarea
          ref={textareaRef}
          value={value}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          disabled={isBusy}
          placeholder={placeholder}
          rows={1}
          className="flex-1 resize-none bg-transparent text-[13px] text-[#111111] placeholder-[#BBBBBB] outline-none disabled:opacity-40"
          style={{ minHeight: "22px", maxHeight: "144px" }}
          aria-label="Chat input"
        />

        <button
          onClick={handleSubmit}
          disabled={!hasContent || isBusy}
          className="mb-0.5 flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-xl transition-all duration-150 disabled:cursor-not-allowed"
          style={{
            background: hasContent && !isBusy ? "#111111" : "#F0F0F0",
            color: hasContent && !isBusy ? "#FFFFFF" : "#BBBBBB",
          }}
          aria-label="Send message"
        >
          {isBusy ? (
            <svg className="h-3.5 w-3.5 animate-spin" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-20" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3"/>
              <path className="opacity-70" fill="currentColor" d="M4 12a8 8 0 018-8v4l3-3-3-3V4a10 10 0 100 20v-2a8 8 0 01-8-8z"/>
            </svg>
          ) : (
            <svg className="h-3.5 w-3.5" viewBox="0 0 20 20" fill="currentColor">
              <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z"/>
            </svg>
          )}
        </button>
      </div>

      <p className="mt-2 text-center text-[10px] text-[#CCCCCC]">
        Coach can make mistakes. Please verify important information.
      </p>
    </div>
  );
}
