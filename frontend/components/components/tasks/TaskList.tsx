"use client";

import { Button } from "@/components/components/ui/button";
import { Card, CardContent } from "@/components/components/ui/card";
import { CreateTaskRequest, Task, UpdateTaskRequest } from "@/types/Task";
import { PlusIcon, RefreshCwIcon } from "lucide-react";
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

  if (isLoading) {
    return (
      <Card className="w-full">
        <CardContent className="flex items-center justify-center py-6">
          <RefreshCwIcon className="w-5 h-5 animate-spin mr-2" />
          <span className="text-sm">読み込み中...</span>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="w-full max-w-none">
      {/* Error Display */}
      {error && (
        <ErrorDisplay
          error={error}
          onDismiss={clearError}
          onRetry={fetchTasks}
        />
      )}

      {/* ヘッダー */}
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-lg font-semibold">タスク</h2>
        <div className="flex gap-1">
          <Button
            variant="outline"
            size="sm"
            onClick={fetchTasks}
            aria-label="更新"
            className="h-8 w-8 p-0"
          >
            <RefreshCwIcon className="w-4 h-4" />
          </Button>
          <Button
            onClick={() => setIsTaskFormOpen(true)}
            size="sm"
            aria-label="新規作成"
            className="h-8 w-8 p-0"
          >
            <PlusIcon className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* タブボタン */}
      <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg mb-2">
        <Button
          variant={activeTab === "active" ? "default" : "ghost"}
          size="sm"
          onClick={() => setActiveTab("active")}
          className="flex-1 h-8 text-xs"
        >
          アクティブ ({activeTasks.length})
        </Button>
        <Button
          variant={activeTab === "completed" ? "default" : "ghost"}
          size="sm"
          onClick={() => setActiveTab("completed")}
          className="flex-1 h-8 text-xs"
        >
          完了済み ({completedTasks.length})
        </Button>
      </div>

      {/* タスクコンテンツ */}
      <div className="space-y-2">
        {activeTab === "active" ? (
          activeTasks.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground text-sm">
              📝 タスクがありません
            </div>
          ) : (
            activeTasks.map((task) => (
              <TaskCard
                key={task.uuid}
                task={task}
                isCompleting={completingTasks.has(task.uuid)}
                onToggleComplete={toggleTaskComplete}
                onEdit={handleEditTask}
                onDelete={onDeleteTask || deleteTask}
              />
            ))
          )
        ) : (
          completedTasks.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground text-sm">
              ✅ 完了したタスクがありません
            </div>
          ) : (
            completedTasks.map((task) => (
              <TaskCard
                key={task.uuid}
                task={task}
                isCompleting={false}
                isUncompleting={uncompletingTasks.has(task.uuid)}
                onToggleComplete={toggleTaskComplete}
                onEdit={handleEditTask}
                onDelete={onDeleteTask || deleteTask}
              />
            ))
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
