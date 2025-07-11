"use client";

import { useEffect, useRef } from "react";
import { CHAT_CONSTANTS, CHAT_STYLES } from "../../constants/chatConstants";
import { useMessages } from "../../hooks/useMessages";
import ChatInput from "./ChatInput";
import ChatMessage from "./ChatMessage";

export default function AIChat() {
  const { messages, isLoading, error, sendMessage } = useMessages();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  return (
    <div className={CHAT_STYLES.container}>
      {/* Error */}
      {error && (
        <div className={CHAT_STYLES.errorAlert}>
          <div className={CHAT_STYLES.errorContent} role="alert">
            <p className="font-bold">{CHAT_CONSTANTS.errorTitle}</p>
            <p>{error}</p>
          </div>
        </div>
      )}

      {/* Messages */}
      <div className={CHAT_STYLES.messagesContainer}>
        {messages.length === 0 && !isLoading ? (
          <div className={CHAT_STYLES.emptyState}>
            <h1 className={CHAT_STYLES.emptyStateTitle}>
              {CHAT_CONSTANTS.emptyStateTitle}
            </h1>
            <p>{CHAT_CONSTANTS.emptyStateDescription}</p>
          </div>
        ) : (
          <div className={CHAT_STYLES.messagesList}>
            {messages.map((message) => (
              <ChatMessage
                key={message.id}
                message={message}
              />
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input */}
      <div className={CHAT_STYLES.inputContainer}>
        <ChatInput onSendMessage={sendMessage} isLoading={isLoading} />
      </div>
    </div>
  );
}
