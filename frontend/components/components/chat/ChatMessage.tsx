import 'github-markdown-css/github-markdown-light.css';
import type { Message } from "../../../types/Chat";
import { cn } from "../../lib/utils";
import { MarkdownContent } from "./MarkdownContent";
import { MessageAvatar } from "./MessageAvatar";

interface ChatMessageProps {
  message: Message;
}

const MESSAGE_STYLES = {
  user: "bg-primary text-primary-foreground shadow-md",
  ai: "bg-card border border-border/40 shadow-sm"
} as const;

export default function ChatMessage({ message }: ChatMessageProps) {
  const { content, isUser } = message;

  return (
    <div className={cn(
      "flex items-start gap-4 group",
      isUser ? "justify-end" : "justify-start"
    )}>
      {!isUser && (
        <div className="flex-shrink-0 transition-transform duration-200 group-hover:scale-105">
          <MessageAvatar isUser={false} />
        </div>
      )}

      <div
        className={cn(
          "max-w-[80%] sm:max-w-[75%] rounded-2xl px-5 py-4",
          "transition-all duration-200 ease-out",
          "backdrop-blur-sm",
          isUser
            ? cn(MESSAGE_STYLES.user, "rounded-br-md hover:shadow-lg")
            : cn(MESSAGE_STYLES.ai, "rounded-bl-md hover:shadow-md hover:border-border/60")
        )}
      >
        {isUser ? (
          <p className="text-sm leading-relaxed whitespace-pre-wrap break-words font-medium">
            {content}
          </p>
        ) : (
          <div className="prose prose-sm max-w-none text-foreground">
            <MarkdownContent content={content} />
          </div>
        )}
      </div>

      {isUser && (
        <div className="flex-shrink-0 transition-transform duration-200 group-hover:scale-105">
          <MessageAvatar isUser={true} />
        </div>
      )}
    </div>
  );
}
