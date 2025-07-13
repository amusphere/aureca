"use client";

import { Task } from "@/types/Task";
import { formatTaskExpiry, isTaskExpired } from "@/utils/taskUtils";
import { CalendarIcon, ClockIcon } from "lucide-react";

interface TaskExpiryDisplayProps {
  task: Task;
  formatString?: string;
  showIcon?: boolean;
}

/**
 * Display task expiry date with appropriate icon and styling
 */
export function TaskExpiryDisplay({
  task,
  formatString = 'yyyy年M月d日 HH:mm',
  showIcon = true
}: TaskExpiryDisplayProps) {
  const formattedExpiry = formatTaskExpiry(task, formatString);
  const isExpired = isTaskExpired(task);

  if (!formattedExpiry) return null;

  return (
    <div className="flex items-center gap-2">
      {showIcon && (
        <>
          {isExpired ? (
            <ClockIcon className="w-4 h-4 text-red-500" />
          ) : (
            <CalendarIcon className="w-4 h-4 text-muted-foreground" />
          )}
        </>
      )}
      <span className={`text-sm ${isExpired && !task.completed ? 'text-red-600 font-medium' : 'text-muted-foreground'}`}>
        {formattedExpiry}
      </span>
    </div>
  );
}
