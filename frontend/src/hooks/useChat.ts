/**
 * hooks/useChat.ts — All chat state in one hook.
 *
 * WHY A CUSTOM HOOK INSTEAD OF CONTEXT:
 *   Chat state is local to one conversation view. It doesn't need to
 *   be shared across the whole app tree. A custom hook keeps the
 *   ChatPanel component clean — it just calls useChat() and renders.
 *
 * WHAT IT MANAGES:
 *   - The active conversation ID
 *   - The list of messages (Message[])
 *   - Send status (idle / sending)
 *   - Error state
 *
 * USAGE:
 *   const { messages, status, sendMessage, startNewConversation } = useChat()
 */

import { useCallback, useState } from "react";
import * as chatApi from "@/api/chat";
import type { ChatStatus, Conversation, Message } from "@/types";

interface UseChatReturn {
  conversation: Conversation | null;
  messages: Message[];
  status: ChatStatus;
  error: string | null;
  sendMessage: (content: string) => Promise<void>;
  startNewConversation: () => Promise<void>;
  loadConversation: (id: string) => Promise<void>;
}

export function useChat(): UseChatReturn {
  const [conversation, setConversation] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [status, setStatus] = useState<ChatStatus>("idle");
  const [error, setError] = useState<string | null>(null);

  /** Start a fresh conversation (called when user clicks "New chat"). */
  const startNewConversation = useCallback(async () => {
    setStatus("sending");
    setError(null);
    try {
      const convo = await chatApi.createConversation();
      setConversation(convo);
      setMessages([]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start conversation");
    } finally {
      setStatus("idle");
    }
  }, []);

  /** Load an existing conversation from the sidebar history. */
  const loadConversation = useCallback(async (id: string) => {
    setStatus("sending");
    setError(null);
    try {
      const msgs = await chatApi.getMessages(id);
      setMessages(msgs);
      // We don't have the full Conversation object here, just set the id.
      // The sidebar already has the list — we only need id for subsequent sends.
      setConversation((prev) =>
        prev?.id === id ? prev : { id, title: null, last_message_at: "", created_at: "" },
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load conversation");
    } finally {
      setStatus("idle");
    }
  }, []);

  /**
   * Send a user message and append both the user message and the AI response.
   *
   * If there's no active conversation yet, one is created first.
   * This lets the user just start typing without clicking "New chat".
   */
  const sendMessage = useCallback(
    async (content: string) => {
      if (status !== "idle") return;
      setStatus("sending");
      setError(null);

      try {
        // Auto-create conversation on first message
        let activeConvo = conversation;
        if (!activeConvo) {
          activeConvo = await chatApi.createConversation();
          setConversation(activeConvo);
        }

        const { user_message, assistant_message } = await chatApi.sendMessage({
          conversation_id: activeConvo.id,
          content,
        });

        setMessages((prev) => [...prev, user_message, assistant_message]);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to send message");
      } finally {
        setStatus("idle");
      }
    },
    [conversation, status],
  );

  return {
    conversation,
    messages,
    status,
    error,
    sendMessage,
    startNewConversation,
    loadConversation,
  };
}
