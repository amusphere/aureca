"use client";

import { Button } from "@/components/components/ui/button";
import { Card, CardContent } from "@/components/components/ui/card";
import { CreateTaskRequest, Task, UpdateTaskRequest } from "@/types/Task";
import { PlusIcon, RefreshCwIcon, SparklesIcon, ClipboardList, CheckCheck } from "lucide-react";
import { useState } from "react";
import { useTasks } from "../../hooks/useTasks";
import { ErrorDisplay } from "../commons/ErrorDisplay";
import { LoadingSpinner } from "../commons/LoadingSpinner";
import { EmptyState } from "../commons/EmptyState";
import { TaskCard } from "./TaskCard";
import { TaskForm } from "./TaskForm";

interface TaskListProps {
  onEditTask?: (task: Task) => void;
  onDeleteTask?: (taskId: string) => void;
}

export function TaskList({ onEditTask, onDeleteTask }: TaskListProps) {
  const [activeTab, setActiveTab] = useState("active");
  const [isTaskFormOpen, setIsTaskFormOpen] = useState(false);
  const [editingTask, setEditingTask] = useState<Task | null>(null);
  const [isGeneratingTasks, setIsGeneratingTasks] = useState(false);

  const {
    activeTasks,
    completedTasks,
    isLoading,
    completingTasks,
    uncompletingTasks,
    fetchTasks,
    createTask,
    updateTask,
    toggleTaskComplete,
    deleteTask,
    error,
    clearError,
  } = useTasks();

  const handleCreateTask = async (taskData: CreateTaskRequest) => {
    await createTask(taskData);
    setIsTaskFormOpen(false);
  };

  const handleEditTask = (task: Task) => {
    if (onEditTask) {
      onEditTask(task);
    } else {
      setEditingTask(task);
    }
  };

  const handleUpdateTask = async (taskData: UpdateTaskRequest) => {
    if (editingTask) {
      await updateTask(editingTask.uuid, taskData);
      setEditingTask(null);
    }
  };

  const handleGenerateTasks = async () => {
    setIsGeneratingTasks(true);
    try {
      const response = await fetch('/api/ai/generate-tasks', {
        method: 'POST',
      });

      if (response.ok) {
        const data = await response.json();

        // タスクが生成されたら一覧を更新
        await fetchTasks();

        // 自動生成完了メッセージを表示
        const gmailCount = data.Gmail?.length || 0;
        const calendarCount = data.GoogleCalendar?.length || 0;

        if (gmailCount > 0 || calendarCount > 0) {
          let message = '自動生成完了 ';
          if (gmailCount > 0) {
            message += `Gmail ${gmailCount}件`;
          }
          if (calendarCount > 0) {
            if (gmailCount > 0) message += ' ';
            message += `GoogleCalendar ${calendarCount}件`;
          }

          // トーストメッセージを表示（sonnerを使用）
          const { toast } = await import('sonner');
          toast.success(message);
        } else {
          const { toast } = await import('sonner');
          toast.info('新しいタスクはありませんでした');
        }

        console.log('タスクが自動生成され、一覧を更新しました');
      } else {
        console.error('タスク生成に失敗しました:', response.status);
        const { toast } = await import('sonner');
        toast.error('タスク生成に失敗しました');
        // エラーでもタスク一覧をリフレッシュして最新状態を確認
        await fetchTasks();
      }
    } catch (error) {
      console.error('タスク生成エラー:', error);
      const { toast } = await import('sonner');
      toast.error('タスク生成中にエラーが発生しました');
      // エラーが発生してもタスク一覧をリフレッシュ
      await fetchTasks();
    } finally {
      setIsGeneratingTasks(false);
    }
  };

  // Enhanced loading state with better visual feedback
  if (isLoading || isGeneratingTasks) {
    return (
      <div className="w-full max-w-none">
        <Card className="border-0 shadow-sm bg-gradient-to-br from-background to-muted/20">
          <CardContent className="py-12 px-6">
            <LoadingSpinner
              size="lg"
              variant="default"
              color="primary"
              text={isGeneratingTasks
                ? 'メールやカレンダーからタスクを作成しています...'
                : 'タスクデータを取得しています...'
              }
              className="flex-col"
            />
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="w-full max-w-none space-y-6">
      {/* Error Display with improved spacing */}
      {error && (
        <div className="mb-6">
          <ErrorDisplay
            error={error}
            onDismiss={clearError}
            onRetry={fetchTasks}
          />
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex items-center justify-center gap-2 p-2 bg-muted/20 rounded-lg border border-border/30">
        <Button
          variant="ghost"
          size="sm"
          onClick={fetchTasks}
          disabled={isGeneratingTasks}
          className="h-8 px-3 text-xs hover:bg-accent hover:text-accent-foreground"
        >
          <RefreshCwIcon className="w-3 h-3 mr-1.5" />
          更新
        </Button>
        <div className="w-px h-4 bg-border/50" />
        <Button
          variant="ghost"
          size="sm"
          onClick={handleGenerateTasks}
          disabled={isGeneratingTasks}
          className="h-8 px-3 text-xs hover:bg-accent hover:text-accent-foreground"
        >
          <SparklesIcon className="w-3 h-3 mr-1.5" />
          自動生成
        </Button>
        <div className="w-px h-4 bg-border/50" />
        <Button
          onClick={() => setIsTaskFormOpen(true)}
          size="sm"
          disabled={isGeneratingTasks}
          className="h-8 px-3 text-xs bg-primary hover:bg-primary/90 text-primary-foreground"
        >
          <PlusIcon className="w-3 h-3 mr-1.5" />
          新規作成
        </Button>
      </div>

      {/* Compact Tab Navigation */}
      <div className="flex bg-muted/30 p-0.5 rounded-md">
        <button
          onClick={() => setActiveTab("active")}
          className={`
            flex-1 flex items-center justify-center gap-1 px-2 py-1 rounded text-xs font-medium transition-colors min-w-0
            ${activeTab === "active"
              ? "bg-background text-foreground shadow-sm"
              : "text-muted-foreground hover:text-foreground"
            }
          `}
        >
          <ClipboardList className="w-3 h-3 flex-shrink-0" />
          <span className="truncate">アクティブ</span>
          <span className={`
            px-1 py-0.5 rounded text-xs font-medium flex-shrink-0
            ${activeTab === "active"
              ? "bg-primary/10 text-primary"
              : "bg-muted text-muted-foreground"
            }
          `}>
            {activeTasks.length}
          </span>
        </button>
        <button
          onClick={() => setActiveTab("completed")}
          className={`
            flex-1 flex items-center justify-center gap-1 px-2 py-1 rounded text-xs font-medium transition-colors min-w-0
            ${activeTab === "completed"
              ? "bg-background text-foreground shadow-sm"
              : "text-muted-foreground hover:text-foreground"
            }
          `}
        >
          <CheckCheck className="w-3 h-3 flex-shrink-0" />
          <span className="truncate">完了済み</span>
          <span className={`
            px-1 py-0.5 rounded text-xs font-medium flex-shrink-0
            ${activeTab === "completed"
              ? "bg-green-100 text-green-700"
              : "bg-muted text-muted-foreground"
            }
          `}>
            {completedTasks.length}
          </span>
        </button>
      </div>

      {/* Enhanced Task Content with improved spacing */}
      <div className="space-y-3">
        {activeTab === "active" ? (
          activeTasks.length === 0 ? (
            <EmptyState
              type="no-tasks"
              onAction={() => setIsTaskFormOpen(true)}
              size="md"
              className="border-dashed border-2 border-border/50 bg-gradient-to-br from-background to-muted/20 rounded-lg"
            />
          ) : (
            <div className="space-y-3">
              {activeTasks.map((task) => (
                <TaskCard
                  key={task.uuid}
                  task={task}
                  isCompleting={completingTasks.has(task.uuid)}
                  onToggleComplete={toggleTaskComplete}
                  onEdit={handleEditTask}
                  onDelete={onDeleteTask || deleteTask}
                />
              ))}
            </div>
          )
        ) : (
          completedTasks.length === 0 ? (
            <EmptyState
              type="completed"
              title="完了したタスクがありません"
              description="タスクを完了すると、ここに表示されます。まずはアクティブなタスクを作成してみましょう。"
              actionLabel="アクティブタスクを見る"
              onAction={() => setActiveTab("active")}
              size="md"
              className="border-dashed border-2 border-border/50 bg-gradient-to-br from-background to-muted/20 rounded-lg"
            />
          ) : (
            <div className="space-y-3">
              {completedTasks.map((task) => (
                <TaskCard
                  key={task.uuid}
                  task={task}
                  isCompleting={false}
                  isUncompleting={uncompletingTasks.has(task.uuid)}
                  onToggleComplete={toggleTaskComplete}
                  onEdit={handleEditTask}
                  onDelete={onDeleteTask || deleteTask}
                />
              ))}
            </div>
          )
        )}
      </div>

      {/* タスク作成フォーム */}
      <TaskForm
        isOpen={isTaskFormOpen}
        onClose={() => setIsTaskFormOpen(false)}
        onSubmit={handleCreateTask}
      />

      {/* タスク編集フォーム */}
      {editingTask && (
        <TaskForm
          isOpen={!!editingTask}
          task={editingTask}
          onClose={() => setEditingTask(null)}
          onSubmit={handleUpdateTask}
        />
      )}
    </div>
  );
}
