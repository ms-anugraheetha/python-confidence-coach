import { useDashboard } from "@/hooks/useDashboard";
import { SkillScoreWidget } from "./SkillScoreWidget";
import { LearningStreakWidget } from "./LearningStreakWidget";
import { RecentAchievementsWidget } from "./RecentAchievementsWidget";
import { MasteredConceptsWidget } from "./MasteredConceptsWidget";
import { NeedsReinforcementWidget } from "./NeedsReinforcementWidget";
import { NextChallengeWidget } from "./NextChallengeWidget";

interface DashboardSidebarProps {
  refreshTrigger?: number;
}

function SkeletonBlock({ h = "h-24" }: { h?: string }) {
  return (
    <div
      className={`${h} animate-pulse rounded-2xl`}
      style={{ background: "#F0F0F0" }}
    />
  );
}

export function DashboardSidebar({ refreshTrigger }: DashboardSidebarProps) {
  const { data, isLoading } = useDashboard();

  void refreshTrigger;

  return (
    <aside
      className="flex h-full w-sidebar flex-shrink-0 flex-col"
      style={{ borderLeft: "1px solid #EAEAEA", background: "#FAFAFA" }}
    >
      {/* Header */}
      <div
        className="flex flex-shrink-0 items-center justify-between px-5 py-4"
        style={{ borderBottom: "1px solid #EAEAEA", background: "#FFFFFF" }}
      >
        <span className="text-[12px] font-semibold text-[#111111]">
          Your Progress
        </span>
        <button className="text-[12px] font-medium text-[#999999] transition-colors hover:text-[#111111]">
          View all
        </button>
      </div>

      {/* Widgets */}
      <div className="flex flex-1 flex-col gap-3 overflow-y-auto px-4 py-4">
        {isLoading || !data ? (
          <>
            <SkeletonBlock h="h-44" />
            <SkeletonBlock h="h-28" />
            <SkeletonBlock h="h-24" />
            <SkeletonBlock h="h-20" />
            <SkeletonBlock h="h-20" />
          </>
        ) : (
          <>
            <SkillScoreWidget
              data={{
                overall_score: data.overall_score,
                topics_explored: data.topics_explored,
              }}
            />
            <LearningStreakWidget
              data={{
                learning_streak: data.learning_streak,
                longest_streak: data.longest_streak,
              }}
            />
            <RecentAchievementsWidget achievements={data.recent_achievements} />
            <MasteredConceptsWidget concepts={data.mastered_concepts} />
            <NeedsReinforcementWidget topics={data.needs_reinforcement} />
            <NextChallengeWidget topic={data.recommended_next} />
          </>
        )}
      </div>
    </aside>
  );
}
