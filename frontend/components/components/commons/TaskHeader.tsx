"use client";

import { Button } from "@/components/components/ui/button";
import { Task } from "@/types/Task";
import { Pencil, Trash2 } from "lucide-react";
import { TaskExpiryDisplay } from "../tasks/TaskExpiryDisplay";
import { TaskStatusBadge } from "../tasks/TaskStatusBadge";

interface TaskHeaderProps {
  task: Task;
  onEdit?: () => void;
  onDelete?: () => void;
  showActions?: boolean;
}

/**
 * Common component for displaying task header with title, status, expiry, and actions
 */
export function TaskHeader({ task, onEdit, onDelete, showActions = true }: TaskHeaderProps) {
  return (
    <div className="flex items-start justify-between gap-4 mb-6">
      <div className="flex-1 min-w-0">
        <h1 className="text-2xl font-bold mb-2 break-words">{task.title}</h1>
        <div className="flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
          <TaskStatusBadge task={task} />
          <TaskExpiryDisplay task={task} />
        </div>
      </div>

      {showActions && (
        <div className="flex gap-2 flex-shrink-0">
          {onEdit && (
            <Button
              variant="ghost"
              size="sm"
              onClick={onEdit}
              className="h-8 w-8 p-0 hover:bg-gray-100"
            >
              <Pencil className="h-4 w-4 text-gray-600" />
            </Button>
          )}

          {onDelete && (
            <Button
              variant="ghost"
              size="sm"
              onClick={onDelete}
              className="h-8 w-8 p-0 hover:bg-red-50 text-red-600 hover:text-red-700"
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          )}
        </div>
      )}
    </div>
  );
}
