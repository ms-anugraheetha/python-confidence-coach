/**
 * hooks/useConversations.ts — Manages the conversation list for the sidebar.
 *
 * Fetches on mount and exposes a `refresh()` so CoachPage can trigger
 * a reload after a new conversation is created or a message is sent.
 */

import { useCallback, useEffect, useState } from "react";
import { listConversations } from "@/api/chat";
import type { Conversation } from "@/types";

interface UseConversationsReturn {
  conversations: Conversation[];
  isLoading: boolean;
  refresh: () => void;
}

export function useConversations(): UseConversationsReturn {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);

    listConversations()
      .then((list) => {
        if (!cancelled) setConversations(list);
      })
      .catch(() => {
        // Silently ignore — sidebar is non-critical
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [refreshKey]);

  const refresh = useCallback(() => setRefreshKey((k) => k + 1), []);

  return { conversations, isLoading, refresh };
}
