/**
 * pages/ProgressPage.tsx — Detailed progress view.
 *
 * Full-page breakdown of the user's skill scores, streak, mastered
 * topics, and areas that need reinforcement.
 */

import { LeftNav } from "@/components/LeftNav";
import { useDashboard } from "@/hooks/useDashboard";
import { SkillScoreWidget } from "@/components/dashboard/SkillScoreWidget";
import { LearningStreakWidget } from "@/components/dashboard/LearningStreakWidget";
import { RecentAchievementsWidget } from "@/components/dashboard/RecentAchievementsWidget";
import { MasteredConceptsWidget } from "@/components/dashboard/MasteredConceptsWidget";
import { NeedsReinforcementWidget } from "@/components/dashboard/NeedsReinforcementWidget";

function SkeletonBlock({ h = "h-24" }: { h?: string }) {
  return (
    <div
      className={`${h} animate-pulse rounded-2xl`}
      style={{ background: "#F0F0F0" }}
    />
  );
}

export function ProgressPage() {
  const { data, isLoading, refresh } = useDashboard();

  return (
    <div className="flex h-screen overflow-hidden" style={{ background: "#FAFAFA" }}>

      {/* Left nav (desktop) */}
      <div className="hidden lg:flex">
        <LeftNav />
      </div>

      {/* Main content */}
      <div className="flex flex-1 flex-col overflow-hidden">

        {/* Mobile top bar */}
        <div
          className="flex flex-shrink-0 items-center px-5 py-3.5 lg:hidden"
          style={{ background: "#FFFFFF", borderBottom: "1px solid #EAEAEA" }}
        >
          <div className="flex items-center gap-2.5">
            <div
              className="flex h-7 w-7 items-center justify-center rounded-lg"
              style={{ background: "#111111" }}
            >
              <svg width="13" height="13" viewBox="0 0 16 16" fill="none">
                <circle cx="5" cy="8" r="3" fill="white" fillOpacity="0.9"/>
                <circle cx="11" cy="8" r="3" fill="white" fillOpacity="0.5"/>
              </svg>
            </div>
            <span className="text-[13px] font-bold text-[#111111]">Progress</span>
          </div>
        </div>

        {/* Scrollable content */}
        <div className="flex-1 overflow-y-auto px-6 py-8 lg:px-10">
          <div className="mx-auto max-w-3xl">

            {/* Header */}
            <div className="mb-8 flex items-center justify-between">
              <div>
                <h1
                  className="text-[24px] font-bold text-[#111111]"
                  style={{ letterSpacing: "-0.02em" }}
                >
                  Your Progress
                </h1>
                <p className="mt-1 text-[14px] text-[#999999]">
                  A breakdown of every topic you've explored.
                </p>
              </div>
              <button
                onClick={refresh}
                className="flex items-center gap-1.5 rounded-xl px-3 py-2 text-[12px] font-medium text-[#666666] transition-colors hover:bg-[#F0F0F0] hover:text-[#111111]"
              >
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 11-2.12-9.36L23 10"/>
                </svg>
                Refresh
              </button>
            </div>

            {isLoading || !data ? (
              <div className="flex flex-col gap-4">
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                  <SkeletonBlock h="h-52" />
                  <SkeletonBlock h="h-52" />
                </div>
                <SkeletonBlock h="h-28" />
                <SkeletonBlock h="h-32" />
                <SkeletonBlock h="h-32" />
              </div>
            ) : (
              <div className="flex flex-col gap-4">
                {/* Top row: score + streak */}
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
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
                </div>

                {/* Mastered + needs reinforcement */}
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                  <MasteredConceptsWidget concepts={data.mastered_concepts} />
                  <NeedsReinforcementWidget topics={data.needs_reinforcement} />
                </div>

                {/* Achievements full-width */}
                <RecentAchievementsWidget achievements={data.recent_achievements} />
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
