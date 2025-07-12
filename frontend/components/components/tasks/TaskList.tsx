"use client";

import { Button } from "@/components/components/ui/button";
import { Card, CardContent } from "@/components/components/ui/card";
import { Task } from "@/types/Task";
import { PlusIcon, RefreshCwIcon } from "lucide-react";
import { useEffect, useState } from "react";
import { TaskCard } from "./TaskCard";

interface TaskListProps {
  onCreateTask?: () => void;
  onEditTask?: (task: Task) => void;
  onDeleteTask?: (taskId: string) => void;
}

export function TaskList({ onCreateTask, onEditTask, onDeleteTask }: TaskListProps) {
  const [activeTasks, setActiveTasks] = useState<Task[]>([]);
  const [completedTasks, setCompletedTasks] = useState<Task[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("active");

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
      // UUIDから実際のタスクIDを取得する必要があります
      // 今回は簡易的に、タスクリストから該当するタスクを見つけます
      const allTasks = [...activeTasks, ...completedTasks];
      const task = allTasks.find(t => t.uuid === taskUuid);

      if (!task) return;

      // 仮のtaskIdとしてUUIDを使用（実際のAPIではIDが必要）
      // これは後でバックエンドのAPIレスポンスにIDフィールドを追加する必要があります
      if (completed) {
        // await completeTask(task.id);
      } else {
        // await incompleteTask(task.id);
      }

      // 楽観的更新
      if (completed) {
        setActiveTasks(prev => prev.filter(t => t.uuid !== taskUuid));
        setCompletedTasks(prev => [...prev, { ...task, completed: true }]);
      } else {
        setCompletedTasks(prev => prev.filter(t => t.uuid !== taskUuid));
        setActiveTasks(prev => [...prev, { ...task, completed: false }]);
      }
    } catch (error) {
      console.error("Failed to toggle task completion:", error);
      // エラー時は元の状態に戻す
      await fetchTasks();
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
          {onCreateTask && (
            <Button
              onClick={onCreateTask}
              size="sm"
              aria-label="新規作成"
              className="h-8 w-8 p-0"
            >
              <PlusIcon className="w-4 h-4" />
            </Button>
          )}
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
                onToggleComplete={handleToggleComplete}
                onEdit={onEditTask}
                onDelete={onDeleteTask}
              />
            ))
          )
        )}
      </div>
    </div>
  );
}
