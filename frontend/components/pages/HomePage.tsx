"use client";

import { TaskList } from "@/components/components/tasks/TaskList";
import { useState } from "react";
import AIChatModal from "../components/chat/AIChatModal";
import FloatingChatButton from "../components/chat/ChatButton";

export default function HomePage() {
  const [isChatOpen, setIsChatOpen] = useState(false);

  const openChat = () => setIsChatOpen(true);
  const closeChat = () => setIsChatOpen(false);

  return (
    <div className="relative h-full bg-background">
      {/* Main Content Area */}
      <main className="h-full overflow-y-auto">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8 pb-24">
          <div className="max-w-6xl mx-auto space-y-6 sm:space-y-8">
            {/* タスク管理セクション */}
            <TaskList />
          </div>
        </div>
      </main>

      {/* Floating Chat Button */}
      <FloatingChatButton
        onClick={openChat}
        hasUnreadMessages={false}
      />

      {/* AI Chat Modal */}
      <AIChatModal
        isOpen={isChatOpen}
        onClose={closeChat}
      />
    </div>
  );
}
