/**
 * hooks/useDashboard.ts — Dashboard data fetching.
 *
 * Fetches on mount and re-fetches whenever `refreshKey` changes.
 * The chat hook bumps `refreshKey` after each AI response so the
 * dashboard reflects the latest skill scores without a full page reload.
 *
 * USAGE:
 *   const { data, isLoading, refresh } = useDashboard()
 */

import { useCallback, useEffect, useState } from "react";
import { getDashboard } from "@/api/dashboard";
import type { DashboardData } from "@/types";

interface UseDashboardReturn {
  data: DashboardData | null;
  isLoading: boolean;
  error: string | null;
  refresh: () => void;
}

export function useDashboard(): UseDashboardReturn {
  const [data, setData] = useState<DashboardData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);

    getDashboard()
      .then((d) => {
        if (!cancelled) setData(d);
      })
      .catch((err: unknown) => {
        if (!cancelled)
          setError(err instanceof Error ? err.message : "Failed to load dashboard");
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [refreshKey]);

  const refresh = useCallback(() => setRefreshKey((k) => k + 1), []);

  return { data, isLoading, error, refresh };
}
