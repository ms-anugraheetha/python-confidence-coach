/**
 * pages/HomePage.tsx — Dashboard overview.
 *
 * Full-width landing page showing the user's learning stats at a glance,
 * with a quick-action card to jump into Chat Coach.
 */

import { useNavigate } from "react-router-dom";
import { LeftNav } from "@/components/LeftNav";
import { useAuth } from "@/context/AuthContext";
import { useDashboard } from "@/hooks/useDashboard";
import { SkillScoreWidget } from "@/components/dashboard/SkillScoreWidget";
import { LearningStreakWidget } from "@/components/dashboard/LearningStreakWidget";
import { RecentAchievementsWidget } from "@/components/dashboard/RecentAchievementsWidget";
import { MasteredConceptsWidget } from "@/components/dashboard/MasteredConceptsWidget";
import { NeedsReinforcementWidget } from "@/components/dashboard/NeedsReinforcementWidget";
import { NextChallengeWidget } from "@/components/dashboard/NextChallengeWidget";

function SkeletonBlock({ h = "h-24" }: { h?: string }) {
  return (
    <div
      className={`${h} animate-pulse rounded-2xl`}
      style={{ background: "#F0F0F0" }}
    />
  );
}

function greeting(name: string): string {
  const hour = new Date().getHours();
  if (hour < 12) return `Good morning, ${name}`;
  if (hour < 18) return `Good afternoon, ${name}`;
  return `Good evening, ${name}`;
}

export function HomePage() {
  const { user } = useAuth();
  const { data, isLoading } = useDashboard();
  const navigate = useNavigate();

  const firstName = user?.display_name?.split(" ")[0] ?? "there";
  const today = new Date().toLocaleDateString("en-US", {
    weekday: "long",
    month: "long",
    day: "numeric",
  });

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
            <span className="text-[13px] font-bold text-[#111111]">Python Confidence Coach</span>
          </div>
        </div>

        {/* Scrollable page content */}
        <div className="flex-1 overflow-y-auto px-6 py-8 lg:px-10">
          <div className="mx-auto max-w-3xl">

            {/* Header */}
            <div className="mb-8">
              <p className="text-[12px] font-medium text-[#BBBBBB]">{today}</p>
              <h1
                className="mt-1 text-[24px] font-bold text-[#111111]"
                style={{ letterSpacing: "-0.02em" }}
              >
                {greeting(firstName)} 👋
              </h1>
              <p className="mt-1 text-[14px] text-[#999999]">
                Here's where your Python journey stands.
              </p>
            </div>

            {/* Quick action card */}
            <button
              onClick={() => navigate("/coach")}
              className="mb-8 w-full rounded-2xl p-5 text-left transition-all hover:opacity-90 active:scale-[0.99]"
              style={{ background: "#111111" }}
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-[11px] font-semibold uppercase tracking-[0.08em] text-[#555555]">
                    Continue Learning
                  </p>
                  <p className="mt-1 text-[16px] font-bold text-white" style={{ letterSpacing: "-0.02em" }}>
                    Open Chat Coach →
                  </p>
                  <p className="mt-0.5 text-[12px] text-[#666666]">
                    Ask a Python question to keep your streak going
                  </p>
                </div>
                <div
                  className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-xl"
                  style={{ background: "rgba(255,255,255,0.08)" }}
                >
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/>
                  </svg>
                </div>
              </div>
            </button>

            {/* Dashboard widgets grid */}
            {isLoading || !data ? (
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <SkeletonBlock h="h-52" />
                <SkeletonBlock h="h-52" />
                <SkeletonBlock h="h-28" />
                <SkeletonBlock h="h-28" />
                <SkeletonBlock h="h-24" />
                <SkeletonBlock h="h-24" />
              </div>
            ) : (
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
                <div className="sm:col-span-2">
                  <NextChallengeWidget topic={data.recommended_next} />
                </div>
                <MasteredConceptsWidget concepts={data.mastered_concepts} />
                <NeedsReinforcementWidget topics={data.needs_reinforcement} />
                <div className="sm:col-span-2">
                  <RecentAchievementsWidget achievements={data.recent_achievements} />
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
