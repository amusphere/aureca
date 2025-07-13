"use client";

import { Button } from "@/components/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/components/ui/card";
import { Task } from "@/types/Task";
import { PlusIcon, RefreshCwIcon } from "lucide-react";
import { TaskCard } from "./TaskCard";

interface TaskSectionProps {
  title: string;
  tasks: Task[];
  isLoading?: boolean;
  emptyMessage: string;
  showCreateButton?: boolean;
  completingTasks?: Set<string>;
  uncompletingTasks?: Set<string>;
  onToggleComplete?: (taskUuid: string, completed: boolean) => Promise<void>;
  onRefresh?: () => Promise<void>;
  onCreateTask?: () => void;
}

/**
 * Unified task section component following AGENTS.md structure
 * Reduces duplication in task display logic
 */
export function TaskSection({
  title,
  tasks,
  isLoading = false,
  emptyMessage,
  showCreateButton = false,
  completingTasks = new Set(),
  uncompletingTasks = new Set(),
  onToggleComplete,
  onRefresh,
  onCreateTask,
}: TaskSectionProps) {
  return (
    <Card className="w-full">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
        <CardTitle className="text-lg font-medium">{title}</CardTitle>
        <div className="flex items-center gap-2">
          {showCreateButton && onCreateTask && (
            <Button
              onClick={onCreateTask}
              size="sm"
              className="bg-blue-600 hover:bg-blue-700 text-white"
            >
              <PlusIcon className="w-4 h-4 mr-1" />
              追加
            </Button>
          )}
          {onRefresh && (
            <Button
              onClick={onRefresh}
              disabled={isLoading}
              variant="outline"
              size="sm"
            >
              <RefreshCwIcon
                className={`w-4 h-4 ${isLoading ? "animate-spin" : ""}`}
              />
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="flex items-center justify-center py-6">
            <RefreshCwIcon className="w-5 h-5 animate-spin mr-2" />
            <span className="text-sm">読み込み中...</span>
          </div>
        ) : tasks.length === 0 ? (
          <div className="text-center py-6 text-muted-foreground">
            {emptyMessage}
          </div>
        ) : (
          <div className="space-y-3">
            {tasks.map((task) => (
              <TaskCard
                key={task.uuid}
                task={task}
                onToggleComplete={onToggleComplete}
                isCompleting={completingTasks.has(task.uuid)}
                isUncompleting={uncompletingTasks.has(task.uuid)}
              />
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
