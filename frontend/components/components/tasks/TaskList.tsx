"use client";

import { Button } from "@/components/components/ui/button";
import { CreateTaskRequest, Task, UpdateTaskRequest } from "@/types/Task";
import { CheckCheck, ClipboardList, PlusIcon, RefreshCwIcon, SparklesIcon } from "lucide-react";
import { useEffect, useState } from "react";
import { useAccessibility } from "../../hooks/useAccessibility";
import { useTasks } from "../../hooks/useTasks";
import { EmptyState } from "../commons/EmptyState";
import { ErrorDisplay } from "../commons/ErrorDisplay";
import { LoadingSpinner } from "../commons/LoadingSpinner";
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

  // 初期データ読み込み完了フラグ（チラつき防止）
  const [hasInitiallyLoaded, setHasInitiallyLoaded] = useState(false);

  // アクセシビリティフック
  const { announce } = useAccessibility();

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

  // 初期データ読み込み完了を管理（チラつき防止）
  useEffect(() => {
    if (!isLoading && !isGeneratingTasks) {
      setHasInitiallyLoaded(true);
    }
  }, [isLoading, isGeneratingTasks]);

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

        // タスクが自動生成され、一覧を更新しました
      } else {
        const { toast } = await import('sonner');
        toast.error('タスク生成に失敗しました');
        // エラーでもタスク一覧をリフレッシュして最新状態を確認
        await fetchTasks();
      }
    } catch {
      const { toast } = await import('sonner');
      toast.error('タスク生成中にエラーが発生しました');
      // エラーが発生してもタスク一覧をリフレッシュ
      await fetchTasks();
    } finally {
      setIsGeneratingTasks(false);
    }
  };

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

      {/* Action Buttons with enhanced accessibility */}
      <div className="flex items-center justify-center gap-2 p-2 bg-muted/20 rounded-lg border border-border/30" role="toolbar" aria-label="タスク操作">
        <Button
          variant="ghost"
          size="sm"
          onClick={fetchTasks}
          disabled={isLoading || isGeneratingTasks}
          aria-label="タスク一覧を更新"
          className="h-8 px-3 text-xs hover:bg-accent hover:text-accent-foreground transition-all duration-300 ease-out hover:scale-105 active:scale-95"
        >
          <RefreshCwIcon className={`w-3 h-3 mr-1.5 transition-transform duration-300 ${isLoading || isGeneratingTasks ? 'animate-spin' : ''}`} aria-hidden="true" />
          <span className="hidden sm:inline">更新</span>
          <span className="sr-only sm:hidden">タスク一覧を更新</span>
        </Button>
        <div className="w-px h-4 bg-border/50" aria-hidden="true" />
        <Button
          variant="ghost"
          size="sm"
          onClick={handleGenerateTasks}
          disabled={isLoading || isGeneratingTasks}
          aria-label="メールやカレンダーからタスクを自動生成"
          aria-busy={isGeneratingTasks}
          className="h-8 px-3 text-xs hover:bg-accent hover:text-accent-foreground transition-all duration-300 ease-out hover:scale-105 active:scale-95"
        >
          <SparklesIcon className={`w-3 h-3 mr-1.5 transition-transform duration-300 ${isGeneratingTasks ? 'animate-pulse' : ''}`} aria-hidden="true" />
          <span className="hidden sm:inline">自動生成</span>
          <span className="sr-only sm:hidden">タスクを自動生成</span>
        </Button>
        <div className="w-px h-4 bg-border/50" aria-hidden="true" />
        <Button
          onClick={() => setIsTaskFormOpen(true)}
          size="sm"
          disabled={isLoading || isGeneratingTasks}
          aria-label="新しいタスクを作成"
          className="h-8 px-3 text-xs bg-primary hover:bg-primary/90 text-primary-foreground transition-all duration-300 ease-out hover:scale-105 active:scale-95 hover:shadow-md"
        >
          <PlusIcon className="w-3 h-3 mr-1.5 transition-transform duration-200" aria-hidden="true" />
          <span className="hidden sm:inline">新規作成</span>
          <span className="sr-only sm:hidden">新しいタスクを作成</span>
        </Button>
      </div>

      {/* Enhanced Tab Navigation with accessibility */}
      <div role="tablist" className="flex bg-muted/30 p-0.5 rounded-md" aria-label="タスクフィルター">
        <button
          role="tab"
          aria-selected={activeTab === "active"}
          aria-controls="active-tasks-panel"
          id="active-tasks-tab"
          onClick={() => {
            setActiveTab("active");
            announce(`アクティブタスクタブに切り替えました。${activeTasks.length}件のタスクがあります。`);
          }}
          className={`
            flex-1 flex items-center justify-center gap-1 px-2 py-1 rounded text-xs font-medium transition-all duration-300 ease-out min-w-0 hover:scale-105 active:scale-95 focus-ring
            ${activeTab === "active"
              ? "bg-background text-foreground shadow-sm"
              : "text-muted-foreground hover:text-foreground hover:bg-background/50"
            }
          `}
        >
          <ClipboardList className="w-3 h-3 flex-shrink-0 transition-transform duration-200" aria-hidden="true" />
          <span className="truncate">アクティブ</span>
          <span
            className={`
              px-1 py-0.5 rounded text-xs font-medium flex-shrink-0 transition-all duration-200
              ${activeTab === "active"
                ? "bg-primary/10 text-primary"
                : "bg-muted text-muted-foreground"
              }
            `}
            aria-label={`${activeTasks.length}件のアクティブタスク`}
          >
            {activeTasks.length}
          </span>
        </button>
        <button
          role="tab"
          aria-selected={activeTab === "completed"}
          aria-controls="completed-tasks-panel"
          id="completed-tasks-tab"
          onClick={() => {
            setActiveTab("completed");
            announce(`完了済みタスクタブに切り替えました。${completedTasks.length}件のタスクがあります。`);
          }}
          className={`
            flex-1 flex items-center justify-center gap-1 px-2 py-1 rounded text-xs font-medium transition-all duration-300 ease-out min-w-0 hover:scale-105 active:scale-95 focus-ring
            ${activeTab === "completed"
              ? "bg-background text-foreground shadow-sm"
              : "text-muted-foreground hover:text-foreground hover:bg-background/50"
            }
          `}
        >
          <CheckCheck className="w-3 h-3 flex-shrink-0 transition-transform duration-200" aria-hidden="true" />
          <span className="truncate">完了済み</span>
          <span
            className={`
              px-1 py-0.5 rounded text-xs font-medium flex-shrink-0 transition-all duration-200
              ${activeTab === "completed"
                ? "bg-green-100 text-green-700"
                : "bg-muted text-muted-foreground"
              }
            `}
            aria-label={`${completedTasks.length}件の完了済みタスク`}
          >
            {completedTasks.length}
          </span>
        </button>
      </div>

      {/* Enhanced Task Content with improved spacing and accessibility */}
      <div className="space-y-3">
        {/* Loading state for task content area only */}
        {isLoading || isGeneratingTasks ? (
          <div className="py-12 px-6 text-center">
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
          </div>
        ) : (
          <div className="relative min-h-[250px]">
            {/* -- Active Tasks Panel (kept mounted) -- */}
            <div
              role="tabpanel"
              id="active-tasks-panel"
              aria-labelledby="active-tasks-tab"
              aria-hidden={activeTab !== "active"}
              className={`
                absolute inset-0
                ${activeTab === "active" ? "opacity-100" : "opacity-0 pointer-events-none"}
              `}
            >
              {activeTasks.length === 0 && hasInitiallyLoaded ? (
                <EmptyState
                  type="no-tasks"
                  onAction={() => setIsTaskFormOpen(true)}
                  size="md"
                  className="border-dashed border-2 border-border/50 bg-gradient-to-br from-background to-muted/20 rounded-lg"
                />
              ) : activeTasks.length > 0 ? (
                <div className="space-y-3" role="list" aria-label="アクティブなタスク一覧">
                  {activeTasks.map((task) => (
                    <div key={task.uuid} role="listitem">
                      <TaskCard
                        task={task}
                        isCompleting={completingTasks.has(task.uuid)}
                        onToggleComplete={toggleTaskComplete}
                        onEdit={handleEditTask}
                        onDelete={onDeleteTask || deleteTask}
                      />
                    </div>
                  ))}
                </div>
              ) : null}
            </div>

            {/* -- Completed Tasks Panel (kept mounted) -- */}
            <div
              role="tabpanel"
              id="completed-tasks-panel"
              aria-labelledby="completed-tasks-tab"
              aria-hidden={activeTab !== "completed"}
              className={`
                absolute inset-0
                ${activeTab === "completed" ? "opacity-100" : "opacity-0 pointer-events-none"}
              `}
            >
              {completedTasks.length === 0 && hasInitiallyLoaded ? (
                <EmptyState
                  type="completed"
                  title="完了したタスクがありません"
                  description="タスクを完了すると、ここに表示されます。まずはアクティブなタスクを作成してみましょう。"
                  actionLabel="アクティブタスクを見る"
                  onAction={() => setActiveTab("active")}
                  size="md"
                  className="border-dashed border-2 border-border/50 bg-gradient-to-br from-background to-muted/20 rounded-lg"
                />
              ) : completedTasks.length > 0 ? (
                <div className="space-y-3" role="list" aria-label="完了済みタスク一覧">
                  {completedTasks.map((task) => (
                    <div key={task.uuid} role="listitem">
                      <TaskCard
                        task={task}
                        isCompleting={false}
                        isUncompleting={uncompletingTasks.has(task.uuid)}
                        onToggleComplete={toggleTaskComplete}
                        onEdit={handleEditTask}
                        onDelete={onDeleteTask || deleteTask}
                      />
                    </div>
                  ))}
                </div>
              ) : null}
            </div>
          </div>
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
