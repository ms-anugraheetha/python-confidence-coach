import { useCallback } from "react";
import { ChatPanel } from "@/components/chat/ChatPanel";
import { ConversationSidebar } from "@/components/chat/ConversationSidebar";
import { LeftNav } from "@/components/LeftNav";
import { useAuth } from "@/context/AuthContext";
import { useChat } from "@/hooks/useChat";
import { useConversations } from "@/hooks/useConversations";

export function CoachPage() {
  const { user } = useAuth();
  const { conversation, messages, status, error, sendMessage, startNewConversation, loadConversation } = useChat();
  const { conversations, isLoading: convsLoading, refresh: refreshConvs } = useConversations();

  // After a message is received, refresh the conversation list so the
  // sidebar shows the latest title and timestamp.
  const handleMessageReceived = useCallback(() => {
    refreshConvs();
  }, [refreshConvs]);

  // Start a new conversation and refresh the sidebar list.
  const handleNewChat = useCallback(async () => {
    await startNewConversation();
    refreshConvs();
  }, [startNewConversation, refreshConvs]);

  // Load an existing conversation from the sidebar.
  const handleSelectConversation = useCallback(async (id: string) => {
    await loadConversation(id);
  }, [loadConversation]);

  return (
    <div className="flex h-screen overflow-hidden" style={{ background: "#FAFAFA" }}>

      {/* Left nav (desktop) */}
      <div className="hidden lg:flex">
        <LeftNav />
      </div>

      {/* Conversation history sidebar (desktop) */}
      <div className="hidden lg:flex">
        <ConversationSidebar
          conversations={conversations}
          activeConversationId={conversation?.id ?? null}
          isLoading={convsLoading}
          onSelect={handleSelectConversation}
          onNew={handleNewChat}
        />
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

        {/* Chat panel */}
        <ChatPanel
          userName={user?.display_name ?? "there"}
          messages={messages}
          status={status}
          error={error}
          onSend={sendMessage}
          onNewChat={handleNewChat}
          onMessageReceived={handleMessageReceived}
        />
      </div>
    </div>
  );
}
