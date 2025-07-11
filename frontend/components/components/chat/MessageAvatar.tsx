import { Bot, User } from 'lucide-react';
import { cn } from "../../lib/utils";

interface MessageAvatarProps {
  isUser: boolean;
  className?: string;
}

const AVATAR_SIZE = "w-8 h-8";
const ICON_SIZE = "w-5 h-5";

const avatarStyles = {
  user: {
    container: "bg-gray-300",
    icon: "text-gray-600"
  },
  ai: {
    container: "bg-gray-200",
    icon: "text-gray-500"
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
