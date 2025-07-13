"use client";

import { Button } from "@/components/components/ui/button";
import { Card, CardContent } from "@/components/components/ui/card";
import { CreateTaskRequest, Task } from "@/types/Task";
import { PlusIcon, RefreshCwIcon } from "lucide-react";
import { useEffect, useState } from "react";
import { TaskCard } from "./TaskCard";
import { TaskForm } from "./TaskForm";

interface TaskListProps {
  onEditTask?: (task: Task) => void;
  onDeleteTask?: (taskId: string) => void;
}

export function TaskList({ onEditTask, onDeleteTask }: TaskListProps) {
  const [activeTasks, setActiveTasks] = useState<Task[]>([]);
  const [completedTasks, setCompletedTasks] = useState<Task[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("active");
  const [completingTasks, setCompletingTasks] = useState<Set<string>>(new Set());
  const [uncompletingTasks, setUncompletingTasks] = useState<Set<string>>(new Set());
  const [isTaskFormOpen, setIsTaskFormOpen] = useState(false);

  const fetchTasks = async () => {
    setIsLoading(true);
    try {
      // アクティブなタスクを取得
      const activeResponse = await fetch("/api/tasks?completed=false");
      if (activeResponse.ok) {
        const activeData = await activeResponse.json();
        setActiveTasks(activeData);
      }

      // 完了済みタスクを取得
      const completedResponse = await fetch("/api/tasks?completed=true");
      if (completedResponse.ok) {
        const completedData = await completedResponse.json();
        setCompletedTasks(completedData);
      }
    } catch (error) {
      console.error("Failed to fetch tasks:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleToggleComplete = async (taskUuid: string, completed: boolean) => {
    try {
      // UUIDから実際のタスクを見つける
      const allTasks = [...activeTasks, ...completedTasks];
      const task = allTasks.find(t => t.uuid === taskUuid);

      if (!task) return;

      // 完了時にアニメーションを開始
      if (completed) {
        setCompletingTasks(prev => new Set([...prev, taskUuid]));
      } else {
        // 未完了に戻すときのアニメーションを開始
        setUncompletingTasks(prev => new Set([...prev, taskUuid]));
      }

      // APIを呼び出してタスクの完了状態を更新（update_task_by_uuidを使用）
      const response = await fetch(`/api/tasks/${taskUuid}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          uuid: task.uuid,
          title: task.title,
          description: task.description,
          completed: completed,
          expires_at: task.expires_at,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to update task');
      }

      // 完了時はアニメーション後に状態を更新
      if (completed) {
        // アニメーション時間を待つ
        setTimeout(() => {
          setActiveTasks(prev => prev.filter(t => t.uuid !== taskUuid));
          setCompletedTasks(prev => [...prev, { ...task, completed: true }]);
          setCompletingTasks(prev => {
            const newSet = new Set(prev);
            newSet.delete(taskUuid);
            return newSet;
          });
        }, 700); // 0.7秒のアニメーション時間
      } else {
        // 未完了に戻すときもアニメーション後に状態を更新
        setTimeout(() => {
          setCompletedTasks(prev => prev.filter(t => t.uuid !== taskUuid));
          setActiveTasks(prev => [...prev, { ...task, completed: false }]);
          setUncompletingTasks(prev => {
            const newSet = new Set(prev);
            newSet.delete(taskUuid);
            return newSet;
          });
        }, 700); // 0.7秒のアニメーション時間
      }
    } catch (error) {
      console.error("Failed to toggle task completion:", error);
      // エラー時は完了中状態をリセット
      setCompletingTasks(prev => {
        const newSet = new Set(prev);
        newSet.delete(taskUuid);
        return newSet;
      });
      // エラー時は未完了中状態もリセット
      setUncompletingTasks(prev => {
        const newSet = new Set(prev);
        newSet.delete(taskUuid);
        return newSet;
      });
      // エラー時は元の状態に戻す
      await fetchTasks();
    }
  };

  const handleCreateTask = async (taskData: CreateTaskRequest) => {
    try {
      const response = await fetch("/api/tasks", {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(taskData),
      });

      if (!response.ok) {
        throw new Error('Failed to create task');
      }

      // タスク作成後、リストを再取得
      await fetchTasks();
    } catch (error) {
      console.error("Failed to create task:", error);
      throw error; // TaskFormでエラーハンドリングできるよう再スロー
    }
  };

  useEffect(() => {
    fetchTasks();
  }, []);

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
                onToggleComplete={handleToggleComplete}
                onEdit={onEditTask}
                onDelete={onDeleteTask}
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
                onToggleComplete={handleToggleComplete}
                onEdit={onEditTask}
                onDelete={onDeleteTask}
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
    </div>
  );
}
