"use client";

import { Button } from "@/components/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/components/ui/card";
import { Task } from "@/types/Task";
import { ArrowLeft, FileText } from "lucide-react";
import { MarkdownContent } from "../components/chat/MarkdownContent";
import { ErrorDisplay } from "../components/commons/ErrorDisplay";
import { TaskHeader } from "../components/commons/TaskHeader";
import { TaskExpiryDisplay } from "../components/tasks/TaskExpiryDisplay";
import { TaskForm } from "../components/tasks/TaskForm";
import { TaskSources } from "../components/tasks/TaskSources";
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
    <div className="w-full max-w-2xl mx-auto px-3 py-3 sm:px-6 sm:py-8 min-h-screen">
      {/* Error display */}
      {error && (
        <ErrorDisplay
          error={error.message}
          onDismiss={clearError}
          onRetry={() => window.location.reload()}
        />
      )}

      <Card className="w-full overflow-hidden shadow-sm border-0 bg-card/50 backdrop-blur-sm">
        <CardHeader className="pb-0 px-4 sm:px-6 pt-4 sm:pt-6">
          <TaskHeader
            task={currentTask}
            onEdit={editTask}
            onDelete={deleteTask}
            subtitle={currentTask.description ? "詳細情報を確認し、タスクを管理できます" : undefined}
          />
        </CardHeader>

        <CardContent className="space-y-6 sm:space-y-8 px-4 sm:px-6 pb-6 sm:pb-8 overflow-hidden">
          {/* Description section */}
          {currentTask.description && (
            <div className="space-y-2 overflow-hidden">
              <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
                <FileText className="w-4 h-4 flex-shrink-0" />
                説明
              </div>
              <div className="pl-3 sm:pl-6 text-sm prose prose-sm max-w-none overflow-hidden">
                <MarkdownContent content={currentTask.description} className="break-words" />
              </div>
            </div>
          )}

          {/* Due date section */}
          {currentTask.expires_at && (
            <div className="space-y-2">
              <div className="text-sm font-medium text-muted-foreground">
                期限
              </div>
              <div className="pl-3 sm:pl-6">
                <TaskExpiryDisplay
                  task={currentTask}
                  formatString="yyyy年M月d日 HH:mm"
                  showIcon={false}
                />
              </div>
            </div>
          )}

          {/* Task sources section */}
          <TaskSources sources={currentTask.sources || []} />

          {/* Enhanced action buttons with improved spacing and styling */}
          <div className="flex flex-col sm:flex-row gap-3 pt-6 border-t border-border/50">
            <Button
              onClick={goBack}
              variant="outline"
              className="flex-1 h-11 sm:h-10 transition-all duration-200 hover:scale-[1.02] hover:shadow-sm"
              disabled={isToggling}
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              戻る
            </Button>
            <Button
              onClick={toggleComplete}
              disabled={isToggling}
              className="flex-1 h-11 sm:h-10 transition-all duration-200 hover:scale-[1.02] hover:shadow-sm"
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
