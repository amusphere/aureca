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
  breadcrumbs?: React.ReactNode;
  subtitle?: string;
}

/**
 * Enhanced task header component with modern design and improved visual hierarchy
 * Features improved spacing, better action button styling, and support for breadcrumbs
 */
export function TaskHeader({
  task,
  onEdit,
  onDelete,
  showActions = true,
  breadcrumbs,
  subtitle
}: TaskHeaderProps) {
  return (
    <div className="space-y-4">
      {/* Breadcrumbs section - if provided */}
      {breadcrumbs && (
        <div className="flex items-center text-sm text-muted-foreground">
          {breadcrumbs}
        </div>
      )}

      {/* Main header content with enhanced spacing and visual hierarchy */}
      <div className="flex items-start justify-between gap-4 sm:gap-6">
        <div className="flex-1 min-w-0 space-y-3">
          {/* Title with improved typography */}
          <div className="space-y-2">
            <h1 className="text-2xl sm:text-3xl font-bold text-foreground leading-tight tracking-tight break-words">
              {task.title}
            </h1>
            {subtitle && (
              <p className="text-base text-muted-foreground leading-relaxed">
                {subtitle}
              </p>
            )}
          </div>

          {/* Status and metadata with enhanced spacing */}
          <div className="flex flex-wrap items-center gap-3 sm:gap-4">
            <TaskStatusBadge task={task} />
            <div className="h-4 w-px bg-border hidden sm:block" />
            <TaskExpiryDisplay task={task} />
          </div>
        </div>

        {/* Enhanced action buttons with better styling */}
        {showActions && (
          <div className="flex items-start gap-2 flex-shrink-0">
            {onEdit && (
              <Button
                variant="ghost"
                size="sm"
                onClick={onEdit}
                className="h-10 w-10 p-0 rounded-lg hover:bg-secondary/80 hover:scale-105 transition-all duration-200 touch-manipulation group"
                aria-label="タスクを編集"
              >
                <Pencil className="h-4 w-4 text-muted-foreground group-hover:text-foreground transition-colors" />
              </Button>
            )}

            {onDelete && (
              <Button
                variant="ghost"
                size="sm"
                onClick={onDelete}
                className="h-10 w-10 p-0 rounded-lg hover:bg-destructive/10 hover:scale-105 transition-all duration-200 touch-manipulation group"
                aria-label="タスクを削除"
              >
                <Trash2 className="h-4 w-4 text-muted-foreground group-hover:text-destructive transition-colors" />
              </Button>
            )}
          </div>
        )}
      </div>

      {/* Subtle section divider */}
      <div className="h-px bg-gradient-to-r from-border via-border/50 to-transparent" />
    </div>
  );
}
