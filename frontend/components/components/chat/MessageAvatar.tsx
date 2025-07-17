import { Bot, User } from 'lucide-react';
import { cn } from "../../lib/utils";

interface MessageAvatarProps {
  isUser: boolean;
  className?: string;
}

const AVATAR_SIZE = "w-9 h-9";
const ICON_SIZE = "w-5 h-5";

const avatarStyles = {
  user: {
    container: "bg-primary/10 border border-primary/20",
    icon: "text-primary"
  },
  ai: {
    container: "bg-muted border border-border/40",
    icon: "text-muted-foreground"
  }
} as const;

export function MessageAvatar({ isUser, className }: MessageAvatarProps) {
  const Icon = isUser ? User : Bot;
  const styles = isUser ? avatarStyles.user : avatarStyles.ai;

  return (
    <div
      className={cn(
        AVATAR_SIZE,
        "rounded-full flex-shrink-0 flex items-center justify-center",
        styles.container,
        className
      )}
    >
      <Icon className={cn(ICON_SIZE, styles.icon)} />
    </div>
  );
}
