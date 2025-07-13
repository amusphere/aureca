"use client";

import { Badge } from "@/components/components/ui/badge";
import { Task } from "@/types/Task";
import { getTaskStatus } from "@/utils/taskUtils";

interface TaskStatusBadgeProps {
  task: Task;
}

/**
 * Display task status badge based on completion and expiry status
 */
export function TaskStatusBadge({ task }: TaskStatusBadgeProps) {
  const { statusText, variant } = getTaskStatus(task);

  return (
    <Badge variant={variant} className="text-xs px-2 py-1">
      {statusText}
    </Badge>
  );
}
