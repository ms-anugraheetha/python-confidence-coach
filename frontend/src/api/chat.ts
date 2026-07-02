/**
 * api/chat.ts — Conversation and message endpoint functions.
 */

import { api } from "@/api/client";
import type {
  Conversation,
  Message,
  SendMessageRequest,
  SendMessageResponse,
} from "@/types";

/** Create a new conversation (empty, no messages yet). */
export async function createConversation(): Promise<Conversation> {
  return api.post<Conversation>("/api/v1/conversations", {});
}

/** Fetch the list of conversations for the sidebar. */
export async function listConversations(): Promise<Conversation[]> {
  return api.get<Conversation[]>("/api/v1/conversations");
}

/** Fetch all messages for a specific conversation. */
export async function getMessages(conversationId: string): Promise<Message[]> {
  return api.get<Message[]>(`/api/v1/conversations/${conversationId}/messages`);
}

/**
 * Send a user message and get the AI response.
 *
 * Returns both the persisted user message and the assistant message.
 * The assistant message has `confidence_check: true` and a populated
 * `check_question` field when the coach has generated a comprehension check.
 */
export async function sendMessage(
  data: SendMessageRequest,
): Promise<SendMessageResponse> {
  return api.post<SendMessageResponse>("/api/v1/chat/message", data);
}
