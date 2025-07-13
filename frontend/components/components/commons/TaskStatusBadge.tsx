"use client";

import { Badge } from "@/components/components/ui/badge";
import { Task } from "@/types/Task";
import { getTaskStatus } from "@/utils/taskUtils";

interface TaskStatusBadgeProps {
  task: Task;
  className?: string;
}

/**
 * Common component for displaying task status badge
 */
export function TaskStatusBadge({ task, className }: TaskStatusBadgeProps) {
  const status = getTaskStatus(task);

  if (!status.isCompleted && !status.isExpired) {
    return null;
  }

  return (
    <Badge
      variant={status.variant}
      className={`text-xs px-1 py-0 ${className || ''}`}
    >
      {status.statusText}
    </Badge>
  );
}
