import type { Achievement, AchievementType } from "@/types";

interface Props {
  achievements: Achievement[];
}

const BADGE_CONFIG: Record<AchievementType, { icon: string; label: string }> = {
  first_concept:     { icon: "◆", label: "First concept" },
  topic_mastered:    { icon: "★", label: "Topic mastered" },
  streak_3:          { icon: "▲", label: "3-day streak" },
  streak_7:          { icon: "▲▲", label: "7-day streak" },
  topic_milestone_5: { icon: "●●", label: "5 topics explored" },
};

function badgeTitle(a: Achievement): string {
  const cfg = BADGE_CONFIG[a.achievement_type];
  if (a.topic) return `${cfg.label}: ${a.topic}`;
  return cfg.label;
}

export function RecentAchievementsWidget({ achievements }: Props) {
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
        Achievements
      </p>

      {achievements.length === 0 ? (
        <p className="text-[11px] text-[#BBBBBB]">
          Your first badge is closer than you think.
        </p>
      ) : (
        <div className="flex flex-col gap-2.5">
          {achievements.slice(0, 4).map((a) => {
            const cfg = BADGE_CONFIG[a.achievement_type];
            return (
              <div key={a.id} className="flex items-center gap-3">
                <span
                  className="flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-lg font-mono text-[10px] font-bold text-[#666666]"
                  style={{ background: "#F4F4F4", border: "1px solid #EAEAEA" }}
                >
                  {cfg.icon}
                </span>
                <span className="text-[12px] font-medium text-[#555555]">
                  {badgeTitle(a)}
                </span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
