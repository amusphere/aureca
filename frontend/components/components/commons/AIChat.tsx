"use client";

import AIChatModal from "../chat/AIChatModal";
import FloatingChatButton from "../chat/ChatButton";

import { useState } from "react";

export default function AIChat() {
  const [isChatOpen, setIsChatOpen] = useState(false);

  const openChat = () => setIsChatOpen(true);
  const closeChat = () => setIsChatOpen(false);

  return (
    <>
      <FloatingChatButton
        onClick={openChat}
        hasUnreadMessages={false}
      />

      {/* AI Chat Modal */}
      <AIChatModal
        isOpen={isChatOpen}
        onClose={closeChat}
      />
    </>
  )
}