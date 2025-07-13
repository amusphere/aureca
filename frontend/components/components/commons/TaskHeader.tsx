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
              variant="outline"
              size="sm"
              onClick={onEdit}
              className="gap-1"
            >
              <Pencil className="h-3 w-3" />
              編集
            </Button>
          )}

          {onDelete && (
            <Button
              variant="outline"
              size="sm"
              onClick={onDelete}
              className="gap-1 text-destructive hover:text-destructive"
            >
              <Trash2 className="h-3 w-3" />
              削除
            </Button>
          )}
        </div>
      )}
    </div>
  );
}
