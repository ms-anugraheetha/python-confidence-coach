import type { SkillScore } from "@/types";

interface Props {
  topics: SkillScore[];
}

export function NeedsReinforcementWidget({ topics }: Props) {
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
        Worth Revisiting
      </p>

      {topics.length === 0 ? (
        <p className="text-[11px] text-[#BBBBBB]">
          No topics need reinforcement yet.
        </p>
      ) : (
        <div className="flex flex-col gap-3">
          {topics.map((s) => (
            <div key={s.topic}>
              <div className="mb-1.5 flex items-center justify-between">
                <span className="text-[12px] font-medium text-[#555555]">{s.topic}</span>
                <span className="font-mono text-[11px] text-[#999999]">
                  {Math.round(s.score)}%
                </span>
              </div>
              <div
                className="h-1.5 w-full overflow-hidden rounded-full"
                style={{ background: "#F0F0F0" }}
              >
                <div
                  className="h-full rounded-full transition-all duration-500"
                  style={{
                    width: `${Math.max(3, s.score)}%`,
                    background: "#111111",
                    opacity: 0.5,
                  }}
                />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
