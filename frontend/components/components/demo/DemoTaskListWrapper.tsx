'use client';

import { useState, useEffect } from 'react';
import { useDemo } from '@/components/contexts/DemoContext';
import { Button } from '@/components/components/ui/button';
import { CheckCheck, ClipboardList, PlusIcon, RefreshCwIcon } from 'lucide-react';
import { TaskCard } from '../tasks/TaskCard';
import { TaskForm } from '../tasks/TaskForm';
import { EmptyState } from '../commons/EmptyState';
import { LoadingSpinner } from '../commons/LoadingSpinner';
import { useAccessibility } from '../../hooks/useAccessibility';
import { Task, CreateTaskRequest, UpdateTaskRequest } from '@/types/Task';
import { DemoTask } from '@/types/Demo';

// DemoTaskをTaskに変換するヘルパー関数
const convertDemoTaskToTask = (demoTask: DemoTask): Task => ({
  uuid: demoTask.id,
  title: demoTask.title,
  description: demoTask.description,
  completed: demoTask.completed,
  expires_at: demoTask.expires_at,
  sources: [{
    uuid: `${demoTask.id}-source`,
    source_type: demoTask.source_type,
    source_url: undefined,
    source_id: undefined,
    title: undefined,
    content: undefined,
    extra_data: undefined,
    created_at: demoTask.created_at,
    updated_at: demoTask.created_at
  }]
});

export function DemoTaskListWrapper() {
  const [activeTab, setActiveTab] = useState("active");
  const [isTaskFormOpen, setIsTaskFormOpen] = useState(false);
  const [editingTask, setEditingTask] = useState<Task | null>(null);
  const [hasInitiallyLoaded, setHasInitiallyLoaded] = useState(false);

  const { announce } = useAccessibility();
  const { state, createTask, updateTask, deleteTask, resetSession } = useDemo();

  useEffect(() => {
    if (state.session && !state.isLoading) {
      setHasInitiallyLoaded(true);
    }
  }, [state.session, state.isLoading]);

  if (!state.session) {
    return (
      <div className="py-12 px-6 text-center">
        <LoadingSpinner
          size="lg"
          variant="default"
          color="primary"
          text="デモ環境を準備中..."
          className="flex-col"
        />
      </div>
    );
  }

  const tasks = state.session.tasks.map(convertDemoTaskToTask);
  const activeTasks = tasks.filter(task => !task.completed);
  const completedTasks = tasks.filter(task => task.completed);

  const handleCreateTask = async (taskData: CreateTaskRequest) => {
    await createTask({
      title: taskData.title,
      description: taskData.description,
      expires_at: taskData.expires_at
    });
    setIsTaskFormOpen(false);
  };

  const handleEditTask = (task: Task) => {
    setEditingTask(task);
  };

  const handleUpdateTask = async (taskData: UpdateTaskRequest) => {
    if (editingTask) {
      await updateTask(editingTask.uuid, {
        title: taskData.title,
        description: taskData.description,
        completed: taskData.completed,
        expires_at: taskData.expires_at
      });
      setEditingTask(null);
    }
  };

  const handleToggleComplete = async (taskUuid: string) => {
    const task = tasks.find(t => t.uuid === taskUuid);
    if (task) {
      await updateTask(taskUuid, { completed: !task.completed });
    }
  };

  const handleDeleteTask = async (taskUuid: string) => {
    await deleteTask(taskUuid);
  };

  return (
    <div className="w-full max-w-none space-y-6">
      {/* Action Buttons - モバイル対応 */}
      <div className="flex items-center justify-center gap-1 sm:gap-2 p-1.5 sm:p-2 bg-muted/20 rounded-lg border border-border/30" role="toolbar" aria-label="タスク操作">
        <Button
          variant="ghost"
          size="sm"
          onClick={resetSession}
          disabled={state.isLoading}
          aria-label="デモをリセット"
          className="h-7 sm:h-8 px-2 sm:px-3 text-xs hover:bg-accent hover:text-accent-foreground transition-all duration-300 ease-out hover:scale-105 active:scale-95"
        >
          <RefreshCwIcon className={`w-3 h-3 mr-1 sm:mr-1.5 transition-transform duration-300 ${state.isLoading ? 'animate-spin' : ''}`} aria-hidden="true" />
          <span className="hidden sm:inline">リセット</span>
          <span className="sr-only sm:hidden">デモをリセット</span>
        </Button>
        <div className="w-px h-3 sm:h-4 bg-border/50" aria-hidden="true" />
        <Button
          onClick={() => setIsTaskFormOpen(true)}
          size="sm"
          disabled={state.isLoading}
          aria-label="新しいタスクを作成"
          className="h-7 sm:h-8 px-2 sm:px-3 text-xs bg-primary hover:bg-primary/90 text-primary-foreground transition-all duration-300 ease-out hover:scale-105 active:scale-95 hover:shadow-md"
        >
          <PlusIcon className="w-3 h-3 mr-1 sm:mr-1.5 transition-transform duration-200" aria-hidden="true" />
          <span className="hidden sm:inline">新規作成</span>
          <span className="sr-only sm:hidden">新しいタスクを作成</span>
        </Button>
      </div>

      {/* Tab Navigation - モバイル対応 */}
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
            flex-1 flex items-center justify-center gap-1 px-1.5 sm:px-2 py-1 rounded text-xs font-medium transition-all duration-300 ease-out min-w-0 hover:scale-105 active:scale-95 focus-ring
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
            flex-1 flex items-center justify-center gap-1 px-1.5 sm:px-2 py-1 rounded text-xs font-medium transition-all duration-300 ease-out min-w-0 hover:scale-105 active:scale-95 focus-ring
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

      {/* Task Content - モバイル対応 */}
      <div className="space-y-2 sm:space-y-3">
        {state.isLoading ? (
          <div className="py-8 sm:py-12 px-4 sm:px-6 text-center">
            <LoadingSpinner
              size="lg"
              variant="default"
              color="primary"
              text="タスクデータを取得しています..."
              className="flex-col"
            />
          </div>
        ) : (
          <div className="relative min-h-[200px] sm:min-h-[250px]">
            {/* Active Tasks Panel */}
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
                <div className="space-y-2 sm:space-y-3" role="list" aria-label="アクティブなタスク一覧">
                  {activeTasks.map((task) => (
                    <div key={task.uuid} role="listitem">
                      <TaskCard
                        task={task}
                        isCompleting={false}
                        onToggleComplete={handleToggleComplete}
                        onEdit={handleEditTask}
                        onDelete={handleDeleteTask}
                      />
                    </div>
                  ))}
                </div>
              ) : null}
            </div>

            {/* Completed Tasks Panel */}
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
                <div className="space-y-2 sm:space-y-3" role="list" aria-label="完了済みタスク一覧">
                  {completedTasks.map((task) => (
                    <div key={task.uuid} role="listitem">
                      <TaskCard
                        task={task}
                        isCompleting={false}
                        isUncompleting={false}
                        onToggleComplete={handleToggleComplete}
                        onEdit={handleEditTask}
                        onDelete={handleDeleteTask}
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