"use client";

import { Button } from "@/components/components/ui/button";
import { Card, CardContent } from "@/components/components/ui/card";
import { CreateTaskRequest, Task, UpdateTaskRequest } from "@/types/Task";
import { PlusIcon, RefreshCwIcon, SparklesIcon, Loader2, ClipboardList, CheckCheck } from "lucide-react";
import { useState } from "react";
import { useTasks } from "../../hooks/useTasks";
import { ErrorDisplay } from "../commons/ErrorDisplay";
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
          <CardContent className="flex flex-col items-center justify-center py-12 px-6">
            <div className="relative mb-4">
              <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center">
                <Loader2 className="w-6 h-6 text-primary animate-spin" />
              </div>
              <div className="absolute inset-0 rounded-full border-2 border-primary/20 animate-pulse"></div>
            </div>
            <div className="text-center space-y-2">
              <p className="text-base font-medium text-foreground">
                {isGeneratingTasks ? 'タスクを自動生成中' : '読み込み中'}
              </p>
              <p className="text-sm text-muted-foreground max-w-xs">
                {isGeneratingTasks
                  ? 'メールやカレンダーからタスクを作成しています...'
                  : 'タスクデータを取得しています...'
                }
              </p>
            </div>
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

      {/* Enhanced Header with better visual hierarchy */}
      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <h2 className="text-xl font-semibold tracking-tight text-foreground">タスク</h2>
          <p className="text-sm text-muted-foreground">
            {activeTasks.length + completedTasks.length > 0
              ? `${activeTasks.length}件のアクティブタスク、${completedTasks.length}件完了`
              : 'タスクを作成して始めましょう'
            }
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={fetchTasks}
            disabled={isGeneratingTasks}
            className="h-9 px-3 hover:bg-accent hover:text-accent-foreground transition-colors"
          >
            <RefreshCwIcon className="w-4 h-4 mr-2" />
            更新
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={handleGenerateTasks}
            disabled={isGeneratingTasks}
            className="h-9 px-3 hover:bg-accent hover:text-accent-foreground transition-colors"
          >
            <SparklesIcon className="w-4 h-4 mr-2" />
            自動生成
          </Button>
          <Button
            onClick={() => setIsTaskFormOpen(true)}
            size="sm"
            disabled={isGeneratingTasks}
            className="h-9 px-3 bg-primary hover:bg-primary-hover text-primary-foreground transition-all duration-200 shadow-sm hover:shadow-md"
          >
            <PlusIcon className="w-4 h-4 mr-2" />
            新規作成
          </Button>
        </div>
      </div>

      {/* Modern Tab Navigation with enhanced styling */}
      <div className="relative">
        <div className="flex space-x-1 bg-muted/50 p-1.5 rounded-xl border border-border/50 backdrop-blur-sm">
          <button
            onClick={() => setActiveTab("active")}
            className={`
              flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all duration-200
              ${activeTab === "active"
                ? "bg-background text-foreground shadow-sm border border-border/50"
                : "text-muted-foreground hover:text-foreground hover:bg-background/50"
              }
            `}
          >
            <ClipboardList className="w-4 h-4" />
            <span>アクティブ</span>
            <span className={`
              px-2 py-0.5 rounded-full text-xs font-medium
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
              flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all duration-200
              ${activeTab === "completed"
                ? "bg-background text-foreground shadow-sm border border-border/50"
                : "text-muted-foreground hover:text-foreground hover:bg-background/50"
              }
            `}
          >
            <CheckCheck className="w-4 h-4" />
            <span>完了済み</span>
            <span className={`
              px-2 py-0.5 rounded-full text-xs font-medium
              ${activeTab === "completed"
                ? "bg-success/10 text-success"
                : "bg-muted text-muted-foreground"
              }
            `}>
              {completedTasks.length}
            </span>
          </button>
        </div>
      </div>

      {/* Enhanced Task Content with improved spacing */}
      <div className="space-y-3">
        {activeTab === "active" ? (
          activeTasks.length === 0 ? (
            <Card className="border-dashed border-2 border-border/50 bg-gradient-to-br from-background to-muted/20">
              <CardContent className="flex flex-col items-center justify-center py-16 px-6">
                <div className="w-16 h-16 rounded-full bg-muted/50 flex items-center justify-center mb-4">
                  <ClipboardList className="w-8 h-8 text-muted-foreground" />
                </div>
                <div className="text-center space-y-2 max-w-sm">
                  <h3 className="text-lg font-medium text-foreground">アクティブなタスクがありません</h3>
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    新しいタスクを作成するか、自動生成機能を使ってメールやカレンダーからタスクを作成しましょう。
                  </p>
                </div>
                <div className="flex gap-2 mt-6">
                  <Button
                    onClick={() => setIsTaskFormOpen(true)}
                    size="sm"
                    className="bg-primary hover:bg-primary-hover text-primary-foreground"
                  >
                    <PlusIcon className="w-4 h-4 mr-2" />
                    タスクを作成
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleGenerateTasks}
                    disabled={isGeneratingTasks}
                  >
                    <SparklesIcon className="w-4 h-4 mr-2" />
                    自動生成
                  </Button>
                </div>
              </CardContent>
            </Card>
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
            <Card className="border-dashed border-2 border-border/50 bg-gradient-to-br from-background to-muted/20">
              <CardContent className="flex flex-col items-center justify-center py-16 px-6">
                <div className="w-16 h-16 rounded-full bg-success/10 flex items-center justify-center mb-4">
                  <CheckCheck className="w-8 h-8 text-success" />
                </div>
                <div className="text-center space-y-2 max-w-sm">
                  <h3 className="text-lg font-medium text-foreground">完了したタスクがありません</h3>
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    タスクを完了すると、ここに表示されます。まずはアクティブなタスクを作成してみましょう。
                  </p>
                </div>
                <Button
                  onClick={() => setActiveTab("active")}
                  variant="outline"
                  size="sm"
                  className="mt-6"
                >
                  <ClipboardList className="w-4 h-4 mr-2" />
                  アクティブタスクを見る
                </Button>
              </CardContent>
            </Card>
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
