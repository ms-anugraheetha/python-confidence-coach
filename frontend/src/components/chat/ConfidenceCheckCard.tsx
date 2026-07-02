import type { Message } from "@/types";
import { MascotAvatar } from "@/components/Mascot";

interface ConfidenceCheckCardProps {
  message: Message;
}

export function ConfidenceCheckCard({ message }: ConfidenceCheckCardProps) {
  const explanation =
    message.check_question && message.content.includes(message.check_question)
      ? message.content.replace(message.check_question, "").trim()
      : message.content;

  return (
    <div className="flex w-full animate-slide-up gap-3">
      <div className="mt-0.5 flex-shrink-0">
        <MascotAvatar size={28} />
      </div>

      <div className="flex w-full max-w-[85%] flex-col gap-3">
        {/* Explanation bubble */}
        {explanation && (
          <div
            className="rounded-3xl rounded-tl-md px-4 py-3.5 text-sm leading-relaxed text-[#333333]"
            style={{
              background: "#FFFFFF",
              border: "1px solid #EAEAEA",
              boxShadow: "0 2px 8px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)",
            }}
          >
            {message.topic_detected && (
              <span
                className="mb-2.5 inline-block rounded-full px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-[0.07em] text-[#999999]"
                style={{ background: "#F4F4F4", border: "1px solid #EAEAEA" }}
              >
                {message.topic_detected}
              </span>
            )}
            <p className="whitespace-pre-wrap">{explanation}</p>
          </div>
        )}

        {/* Comprehension check card */}
        {message.check_question && (
          <div
            className="rounded-3xl px-5 py-4"
            style={{
              background: "#FFFFFF",
              border: "1px solid #EAEAEA",
              borderLeft: "3px solid #111111",
              boxShadow: "0 2px 8px rgba(0,0,0,0.06)",
            }}
          >
            <div className="mb-3 flex items-center gap-2">
              <span
                className="rounded-full px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-[0.1em] text-[#666666]"
                style={{ background: "#F4F4F4" }}
              >
                Comprehension Check
              </span>
            </div>

            <p className="text-[13px] leading-relaxed text-[#333333]">
              {message.check_question}
            </p>

            <p className="mt-3 text-[11px] text-[#BBBBBB]">
              Type your answer below — there's no wrong way to explain it.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
