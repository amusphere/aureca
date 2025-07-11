"use client";

import { Button } from "@/components/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/components/ui/card";
import { Task } from "@/types/Task";
import { apiGet } from "@/utils/api";
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
      const activeResponse = await apiGet<Task[]>("/tasks?completed=false");
      if (activeResponse.data) {
        setActiveTasks(activeResponse.data);
      }

      // 完了済みタスクを取得
      const completedResponse = await apiGet<Task[]>("/tasks?completed=true");
      if (completedResponse.data) {
        setCompletedTasks(completedResponse.data);
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
      <Card>
        <CardContent className="flex items-center justify-center py-8">
          <RefreshCwIcon className="w-6 h-6 animate-spin mr-2" />
          <span>タスクを読み込み中...</span>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>タスク管理</CardTitle>
            <CardDescription>
              タスクを管理し、進捗を追跡できます
            </CardDescription>
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={fetchTasks}
              className="flex items-center gap-2"
            >
              <RefreshCwIcon className="w-4 h-4" />
              更新
            </Button>
            {onCreateTask && (
              <Button
                onClick={onCreateTask}
                size="sm"
                className="flex items-center gap-2"
              >
                <PlusIcon className="w-4 h-4" />
                新規作成
              </Button>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* タブボタン */}
          <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg">
            <Button
              variant={activeTab === "active" ? "default" : "ghost"}
              size="sm"
              onClick={() => setActiveTab("active")}
              className="flex-1"
            >
              アクティブ ({activeTasks.length})
            </Button>
            <Button
              variant={activeTab === "completed" ? "default" : "ghost"}
              size="sm"
              onClick={() => setActiveTab("completed")}
              className="flex-1"
            >
              完了済み ({completedTasks.length})
            </Button>
          </div>

          {/* タスクコンテンツ */}
          <div className="space-y-4">
            {activeTab === "active" ? (
              activeTasks.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  アクティブなタスクはありません
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
                <div className="text-center py-8 text-muted-foreground">
                  完了済みのタスクはありません
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
      </CardContent>
    </Card>
  );
}
