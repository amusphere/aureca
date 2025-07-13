"use client";

import { Task } from "@/types/Task";
import { formatTaskExpiry, isTaskExpired } from "@/utils/taskUtils";
import { Calendar, Clock } from "lucide-react";

interface TaskExpiryDisplayProps {
  task: Task;
  showIcon?: boolean;
  formatString?: string;
  className?: string;
}

/**
 * Common component for displaying task expiry information
 */
export function TaskExpiryDisplay({
  task,
  showIcon = true,
  formatString,
  className = ""
}: TaskExpiryDisplayProps) {
  const formattedExpiry = formatTaskExpiry(task, formatString);

  if (!formattedExpiry) {
    return null;
  }

  const expired = isTaskExpired(task);
  const IconComponent = expired ? Clock : Calendar;
  const iconClass = expired ? "text-red-500" : "text-muted-foreground";
  const textClass = expired && !task.completed ? "text-red-600 font-medium" : "text-muted-foreground";

  return (
    <div className={`flex items-center gap-1 ${className}`}>
      {showIcon && <IconComponent className={`w-3 h-3 ${iconClass}`} />}
      <span className={`text-xs ${textClass}`}>
        {formattedExpiry}
        {expired && !task.completed && (
          <span className="ml-2 text-red-500">(期限切れ)</span>
        )}
      </span>
    </div>
  );
}
