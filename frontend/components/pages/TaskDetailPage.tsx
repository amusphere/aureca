"use client";

import { Button } from "@/components/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/components/ui/card";
import { Task } from "@/types/Task";
import { ArrowLeft, FileText } from "lucide-react";
import { ErrorDisplay } from "../components/commons/ErrorDisplay";
import { TaskHeader } from "../components/commons/TaskHeader";
import { TaskExpiryDisplay } from "../components/tasks/TaskExpiryDisplay";
import { TaskForm } from "../components/tasks/TaskForm";
import { useTaskDetail } from "../hooks/useTaskDetail";

interface TaskDetailPageProps {
  task: Task;
}

/**
 * Task detail page component - displays task information and provides actions
 */
export default function TaskDetailPage({ task }: TaskDetailPageProps) {
  const {
    currentTask,
    isToggling,
    isEditing,
    toggleComplete,
    editTask,
    updateTask,
    deleteTask,
    goBack,
    setIsEditing,
    error,
    clearError,
  } = useTaskDetail(task);

  return (
    <div className="container mx-auto px-6 py-8 max-w-2xl">
      {/* Error display */}
      {error && (
        <ErrorDisplay
          error={error.message}
          onDismiss={clearError}
          onRetry={() => window.location.reload()}
        />
      )}

      <Card className="w-full">
        <CardHeader className="pb-4">
          <TaskHeader
            task={currentTask}
            onEdit={editTask}
            onDelete={deleteTask}
          />
        </CardHeader>

        <CardContent className="space-y-6">
          {/* Description section */}
          {currentTask.description && (
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
                <FileText className="w-4 h-4" />
                説明
              </div>
              <div className="pl-6 text-sm whitespace-pre-wrap">
                {currentTask.description}
              </div>
            </div>
          )}

          {/* Due date section */}
          {currentTask.expires_at && (
            <div className="space-y-2">
              <div className="text-sm font-medium text-muted-foreground">
                期限
              </div>
              <div className="pl-6">
                <TaskExpiryDisplay
                  task={currentTask}
                  formatString="yyyy年M月d日 HH:mm"
                  showIcon={false}
                />
              </div>
            </div>
          )}

          {/* Action buttons */}
          <div className="flex gap-3 pt-4 border-t">
            <Button
              onClick={goBack}
              variant="outline"
              className="flex-1"
              disabled={isToggling}
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              戻る
            </Button>
            <Button
              onClick={toggleComplete}
              disabled={isToggling}
              className="flex-1"
              variant={currentTask.completed ? "outline" : "default"}
            >
              {isToggling
                ? "更新中..."
                : currentTask.completed
                  ? "未完了に戻す"
                  : "完了にする"
              }
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Task Edit Form */}
      <TaskForm
        isOpen={isEditing}
        task={currentTask}
        onClose={() => setIsEditing(false)}
        onSubmit={updateTask}
      />
    </div>
  );
}
