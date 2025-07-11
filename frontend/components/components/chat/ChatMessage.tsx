import 'github-markdown-css/github-markdown-light.css';
import type { Message } from "../../../types/chat";
import { cn } from "../../lib/utils";
import { MarkdownContent } from "./MarkdownContent";
import { MessageAvatar } from "./MessageAvatar";

interface ChatMessageProps {
  message: Message;
}

const MESSAGE_STYLES = {
  user: "bg-blue-600 text-white",
  ai: "bg-white border border-gray-200"
} as const;

export default function ChatMessage({ message }: ChatMessageProps) {
  const { content, isUser } = message;

  return (
    <div className={cn("flex items-start gap-3", isUser ? "justify-end" : "justify-start")}>
      {!isUser && <MessageAvatar isUser={false} />}

      <div
        className={cn(
          "max-w-[85%] rounded-2xl px-4 py-2.5",
          isUser ? MESSAGE_STYLES.user : MESSAGE_STYLES.ai
        )}
      >
        {isUser ? (
          <p className="text-sm whitespace-pre-wrap break-words">{content}</p>
        ) : (
          <MarkdownContent content={content} />
        )}
      </div>

      {isUser && <MessageAvatar isUser={true} />}
    </div>
  );
}
