import type { DashboardData } from "@/types";

interface Props {
  data: Pick<DashboardData, "learning_streak" | "longest_streak">;
}

export function LearningStreakWidget({ data }: Props) {
  const { learning_streak, longest_streak } = data;

  return (
    <div
      className="rounded-2xl px-5 py-4"
      style={{
        background: "#FFFFFF",
        border: "1px solid #EAEAEA",
        boxShadow: "0 1px 3px rgba(0,0,0,0.06)",
      }}
    >
      <p className="mb-3 text-[11px] font-semibold uppercase tracking-[0.08em] text-[#BBBBBB]">
        Learning Streak
      </p>

      <div className="flex items-center gap-3">
        {/* Fire icon — the one allowed color element */}
        <span style={{ fontSize: "1.75rem", lineHeight: 1 }}>🔥</span>
        <div>
          <div className="flex items-baseline gap-1.5">
            <span
              className="font-bold text-[#111111]"
              style={{ fontSize: "2rem", letterSpacing: "-0.03em", lineHeight: 1 }}
            >
              {learning_streak}
            </span>
            <span className="text-[13px] font-medium text-[#666666]">
              day{learning_streak !== 1 ? "s" : ""}
            </span>
          </div>
          {longest_streak > 0 && longest_streak > learning_streak && (
            <p className="mt-0.5 text-[11px] text-[#BBBBBB]">
              Best streak: {longest_streak} day{longest_streak !== 1 ? "s" : ""}
            </p>
          )}
        </div>
      </div>

      {learning_streak === 0 && (
        <p className="mt-2.5 text-[11px] text-[#BBBBBB]">
          Ask a question today to start your streak.
        </p>
      )}
      {learning_streak >= 7 && (
        <p className="mt-2.5 text-[11px] text-[#999999] font-medium">
          One week of consistent learning! 🎉
        </p>
      )}
    </div>
  );
}
