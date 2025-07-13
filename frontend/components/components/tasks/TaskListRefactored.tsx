"use client";

import { Card, CardContent } from "@/components/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/components/ui/tabs";
import { CreateTaskRequest, Task } from "@/types/Task";
import { RefreshCwIcon } from "lucide-react";
import { useState } from "react";
import { useTaskOperations } from "../../hooks/useTaskOperations";
import { ErrorDisplay } from "../commons/ErrorDisplay";
import { TaskForm } from "./TaskForm";
import { TaskSection } from "./TaskSection";

interface TaskListRefactoredProps {
  onEditTask?: (task: Task) => void;
  onDeleteTask?: (taskId: string) => void;
}

/**
 * Refactored TaskList component following AGENTS.md structure
 * Improved maintainability and readability with unified components
 */
export function TaskListRefactored({ onEditTask, onDeleteTask }: TaskListRefactoredProps) {
  const [activeTab, setActiveTab] = useState("active");
  const [isTaskFormOpen, setIsTaskFormOpen] = useState(false);

  const {
    activeTasks,
    completedTasks,
    isLoading,
    completingTasks,
    uncompletingTasks,
    fetchTasks,
    createTask,
    toggleTaskComplete,
    error,
    clearError,
  } = useTaskOperations();

  const handleCreateTask = async (taskData: CreateTaskRequest) => {
    await createTask(taskData);
    setIsTaskFormOpen(false);
  };

  if (isLoading && activeTasks.length === 0 && completedTasks.length === 0) {
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
    <div className="w-full space-y-4">
      {error && (
        <ErrorDisplay
          error={error}
          onDismiss={clearError}
        />
      )}

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="active">
            アクティブ ({activeTasks.length})
          </TabsTrigger>
          <TabsTrigger value="completed">
            完了済み ({completedTasks.length})
          </TabsTrigger>
        </TabsList>

        <TabsContent value="active" className="space-y-4">
          <TaskSection
            title="アクティブなタスク"
            tasks={activeTasks}
            isLoading={isLoading}
            emptyMessage="アクティブなタスクはありません。新しいタスクを作成しましょう。"
            showCreateButton={true}
            completingTasks={completingTasks}
            onToggleComplete={toggleTaskComplete}
            onRefresh={fetchTasks}
            onCreateTask={() => setIsTaskFormOpen(true)}
          />
        </TabsContent>

        <TabsContent value="completed" className="space-y-4">
          <TaskSection
            title="完了済みのタスク"
            tasks={completedTasks}
            isLoading={isLoading}
            emptyMessage="完了済みのタスクはありません。"
            uncompletingTasks={uncompletingTasks}
            onToggleComplete={toggleTaskComplete}
            onRefresh={fetchTasks}
          />
        </TabsContent>
      </Tabs>

      <TaskForm
        isOpen={isTaskFormOpen}
        onClose={() => setIsTaskFormOpen(false)}
        onSubmit={handleCreateTask}
      />
    </div>
  );
}
