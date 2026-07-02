import type { DashboardData } from "@/types";

interface Props {
  data: Pick<DashboardData, "overall_score" | "topics_explored">;
}

function levelLabel(score: number): string {
  if (score >= 90) return "Mastered";
  if (score >= 75) return "Confident";
  if (score >= 50) return "Developing";
  return "Getting started";
}

function levelHint(score: number): string {
  if (score >= 90) return "Real Python confidence built.";
  if (score >= 75) return "Thinking like a Pythonista.";
  if (score >= 50) return "Good progress — keep exploring.";
  if (score > 0) return "Every question makes you stronger.";
  return "Ask your first question to begin.";
}

export function SkillScoreWidget({ data }: Props) {
  const score = Math.round(data.overall_score);
  const radius = 40;
  const circumference = 2 * Math.PI * radius;
  const filled = (score / 100) * circumference;
  const gap = circumference - filled;

  return (
    <div
      className="flex flex-col items-center gap-4 rounded-2xl px-5 py-6"
      style={{
        background: "#FFFFFF",
        border: "1px solid #EAEAEA",
        boxShadow: "0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)",
      }}
    >
      {/* Label */}
      <div className="flex w-full items-center justify-between">
        <span className="text-[11px] font-semibold uppercase tracking-[0.08em] text-[#BBBBBB]">
          Overall Progress
        </span>
        <span
          className="rounded-md px-2 py-0.5 text-[11px] font-bold text-[#111111]"
          style={{ background: "#F4F4F4" }}
        >
          {score}%
        </span>
      </div>

      {/* Circular gauge */}
      <div className="relative flex items-center justify-center">
        <svg width="108" height="108" viewBox="0 0 108 108" className="-rotate-90">
          <circle cx="54" cy="54" r={radius} fill="none" stroke="#F0F0F0" strokeWidth="7" />
          <circle
            cx="54" cy="54" r={radius}
            fill="none"
            stroke="#111111"
            strokeWidth="7"
            strokeLinecap="round"
            strokeDasharray={`${filled} ${gap}`}
            className="transition-all duration-700"
          />
        </svg>
        <div className="absolute text-center">
          <span className="block text-[22px] font-bold text-[#111111]" style={{ letterSpacing: "-0.03em" }}>
            {score}%
          </span>
        </div>
      </div>

      <div className="text-center">
        <p className="text-[13px] font-bold text-[#111111]">{levelLabel(score)}</p>
        <p className="mt-0.5 text-[11px] text-[#999999]">{levelHint(score)}</p>
      </div>

      <div className="w-full pt-3 text-center" style={{ borderTop: "1px solid #F0F0F0" }}>
        <span className="text-[12px] text-[#999999]">
          <span className="font-semibold text-[#111111]">{data.topics_explored}</span>
          {" "}topic{data.topics_explored !== 1 ? "s" : ""} explored
        </span>
      </div>
    </div>
  );
}
