import type { SkillScore } from "@/types";

interface Props {
  concepts: SkillScore[];
}

export function MasteredConceptsWidget({ concepts }: Props) {
  return (
    <div
      className="rounded-2xl px-5 py-4"
      style={{
        background: "#FFFFFF",
        border: "1px solid #EAEAEA",
        boxShadow: "0 1px 3px rgba(0,0,0,0.06)",
      }}
    >
      <div className="mb-3 flex items-center justify-between">
        <p className="text-[11px] font-semibold uppercase tracking-[0.08em] text-[#BBBBBB]">
          Topics Mastered
        </p>
        {concepts.length > 0 && (
          <span
            className="rounded-full px-2 py-0.5 text-[11px] font-bold text-[#111111]"
            style={{ background: "#F4F4F4" }}
          >
            {concepts.length}
          </span>
        )}
      </div>

      {concepts.length === 0 ? (
        <p className="text-[11px] text-[#BBBBBB]">
          Score 90+ on a topic to mark it mastered.
        </p>
      ) : (
        <div className="flex flex-wrap gap-1.5">
          {concepts.map((s) => (
            <span
              key={s.topic}
              className="rounded-full px-3 py-1 text-[11px] font-medium text-[#555555] transition-colors hover:bg-[#111111] hover:text-white"
              style={{ background: "#F4F4F4", border: "1px solid #EAEAEA", cursor: "default" }}
              title={`Score: ${Math.round(s.score)}`}
            >
              {s.topic}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
