/**
 * api/dashboard.ts — Dashboard data endpoint.
 */

import { api } from "@/api/client";
import type { DashboardData } from "@/types";

/**
 * Fetch all dashboard data in a single request.
 *
 * The backend aggregates skill_scores + achievements + streak data
 * into one response so the sidebar loads with one round trip.
 */
export async function getDashboard(): Promise<DashboardData> {
  return api.get<DashboardData>("/api/v1/dashboard");
}
