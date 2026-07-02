/**
 * types/index.ts — All shared TypeScript interfaces.
 *
 * WHY ONE FILE FOR ALL TYPES:
 *   At this project size, one types file is faster to navigate than
 *   a types/ folder with 10 small files. If it grows past ~200 lines
 *   it should be split into auth.ts, chat.ts, dashboard.ts.
 *
 * NAMING:
 *   Interfaces match the FastAPI Pydantic response schemas exactly.
 *   When Phase 7 wires up real API calls, types and responses will
 *   match without translation.
 */

// ── Auth ──────────────────────────────────────────────────────────────────────

export interface User {
  id: string;
  email: string;
  display_name: string;
  created_at: string;
}

export interface AuthTokens {
  access_token: string;
  token_type: "bearer";
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  display_name?: string;
}

// ── Conversations ─────────────────────────────────────────────────────────────

export interface Conversation {
  id: string;
  title: string | null;
  last_message_at: string;
  created_at: string;
}

// ── Messages ──────────────────────────────────────────────────────────────────

/** Mirrors the `role` column in the messages table. */
export type MessageRole = "user" | "assistant";

/**
 * A single message in the chat thread.
 *
 * `confidence_check` is set to true on assistant messages that contain
 * a comprehension check question. The UI renders these differently
 * (ConfidenceCheckCard vs regular MessageBubble).
 *
 * The check question text is always the last part of the assistant message.
 * The frontend receives the full message and a flag — it does not need to
 * parse which part is the explanation and which is the check question.
 */
export interface Message {
  id: string;
  conversation_id: string;
  role: MessageRole;
  content: string;
  topic_detected: string | null;
  /** True when this assistant message ends with a comprehension check question. */
  confidence_check: boolean;
  /** The isolated check question text (only present when confidence_check=true). */
  check_question: string | null;
  created_at: string;
}

/** Shape of the POST /api/v1/chat/message request body. */
export interface SendMessageRequest {
  conversation_id: string;
  content: string;
}

/** Shape of the POST /api/v1/chat/message response. */
export interface SendMessageResponse {
  user_message: Message;
  assistant_message: Message;
}

// ── Dashboard ─────────────────────────────────────────────────────────────────

export type SkillLevel = "beginner" | "developing" | "confident" | "mastered";

export interface SkillScore {
  topic: string;
  score: number;       // 0.0 – 100.0
  level: SkillLevel;
  attempts: number;
  correct_streak: number;
  longest_streak: number;
  last_assessed_at: string | null;
}

export type AchievementType =
  | "first_concept"
  | "topic_mastered"
  | "streak_3"
  | "streak_7"
  | "topic_milestone_5";

export interface Achievement {
  id: string;
  achievement_type: AchievementType;
  topic: string | null;
  earned_at: string;
  metadata_json: Record<string, unknown> | null;
}

/**
 * The full dashboard payload — one request loads everything the sidebar needs.
 * Backend aggregates this from skill_scores + achievements tables.
 */
export interface DashboardData {
  /** Overall score across all topics (weighted average). */
  overall_score: number;
  /** Current daily learning streak (days with at least one check). */
  learning_streak: number;
  /** Longest streak ever. */
  longest_streak: number;
  /** Total topics touched (any score > 0). */
  topics_explored: number;
  /** Recently earned badges, newest first. */
  recent_achievements: Achievement[];
  /** Topics where score >= 90, ordered by score desc. */
  mastered_concepts: SkillScore[];
  /** Topics where score < 50 with at least 1 attempt, ordered by score asc. */
  needs_reinforcement: SkillScore[];
  /** The next topic the coach recommends working on. */
  recommended_next: string | null;
}

// ── UI state ──────────────────────────────────────────────────────────────────

/** Local UI state for the chat input area. */
export type ChatStatus =
  | "idle"         // waiting for user input
  | "sending"      // user hit send, waiting for response
  | "streaming";   // AI is responding (future: streaming support)

/** Sidebar panel visibility on narrow screens. */
export type SidebarTab = "chat" | "dashboard";
