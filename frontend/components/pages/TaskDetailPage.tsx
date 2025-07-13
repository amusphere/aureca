"use client";

import { Badge } from "@/components/components/ui/badge";
import { Button } from "@/components/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/components/ui/card";
import { Task } from "@/types/Task";
import { TaskService } from "@/utils/taskService";
import { isTaskExpired } from "@/utils/taskUtils";
import { format, fromUnixTime } from "date-fns";
import { ja } from "date-fns/locale";
import { ArrowLeft, Calendar, Clock, FileText } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

interface TaskDetailPageProps {
  taskUuid: string;
}

export default function TaskDetailPage({ taskUuid }: TaskDetailPageProps) {
  const router = useRouter();
  const [task, setTask] = useState<Task | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isToggling, setIsToggling] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // タスクの詳細を取得
  useEffect(() => {
    const fetchTask = async () => {
      try {
        setIsLoading(true);
        setError(null);

        const response = await fetch(`/api/tasks/${taskUuid}`);
        if (!response.ok) {
          if (response.status === 404) {
            setError("タスクが見つかりませんでした");
          } else {
            setError("タスクの取得に失敗しました");
          }
          return;
        }

        const taskData = await response.json();
        setTask(taskData);
      } catch (err) {
        setError("タスクの取得中にエラーが発生しました");
        console.error("Failed to fetch task:", err);
      } finally {
        setIsLoading(false);
      }
    };

    if (taskUuid) {
      fetchTask();
    }
  }, [taskUuid]);

  // タスクの完了状態を切り替え
  const handleToggleComplete = async () => {
    if (!task) return;

    try {
      setIsToggling(true);
      const updatedTask = await TaskService.toggleTaskCompletion(task, !task.completed);
      setTask(updatedTask);
    } catch (err) {
      console.error("Failed to toggle task completion:", err);
      setError("タスクの更新に失敗しました");
    } finally {
      setIsToggling(false);
    }
  };

  // 戻るボタンの処理
  const handleGoBack = () => {
    router.back();
  };

  // ローディング状態
  if (isLoading) {
    return (
      <div className="container mx-auto px-6 py-8 max-w-2xl">
        <Card>
          <CardContent className="flex items-center justify-center py-12">
            <div className="text-muted-foreground">読み込み中...</div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // エラー状態
  if (error || !task) {
    return (
      <div className="container mx-auto px-6 py-8 max-w-2xl">
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12 space-y-4">
            <div className="text-red-600 text-center">{error || "タスクが見つかりませんでした"}</div>
            <Button onClick={handleGoBack} variant="outline">
              <ArrowLeft className="w-4 h-4 mr-2" />
              戻る
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const expired = isTaskExpired(task);
  const expiryDate = task.expires_at ? fromUnixTime(task.expires_at) : null;

  return (
    <div className="container mx-auto px-6 py-8 max-w-2xl">
      <Card className="w-full">
        <CardHeader className="pb-4">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <CardTitle className={`text-xl font-semibold ${task.completed ? 'line-through text-muted-foreground' : ''}`}>
                {task.title}
              </CardTitle>
              <div className="flex gap-2 mt-3">
                {task.completed && (
                  <Badge variant="secondary" className="text-xs">
                    完了
                  </Badge>
                )}
                {expired && !task.completed && (
                  <Badge variant="destructive" className="text-xs">
                    期限切れ
                  </Badge>
                )}
              </div>
            </div>
          </div>
        </CardHeader>

        <CardContent className="space-y-6">
          {/* 説明 */}
          {task.description && (
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
                <FileText className="w-4 h-4" />
                説明
              </div>
              <div className="pl-6 text-sm whitespace-pre-wrap">
                {task.description}
              </div>
            </div>
          )}

          {/* 期限 */}
          {expiryDate && (
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
                {expired ? (
                  <Clock className="w-4 h-4 text-red-500" />
                ) : (
                  <Calendar className="w-4 h-4" />
                )}
                期限
              </div>
              <div className={`pl-6 text-sm ${expired && !task.completed ? 'text-red-600 font-medium' : ''}`}>
                {format(expiryDate, 'yyyy年M月d日 HH:mm', { locale: ja })}
                {expired && !task.completed && (
                  <span className="ml-2 text-red-500">(期限切れ)</span>
                )}
              </div>
            </div>
          )}

          {/* アクションボタン */}
          <div className="flex gap-3 pt-4 border-t">
            <Button
              onClick={handleGoBack}
              variant="outline"
              className="flex-1"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              戻る
            </Button>
            <Button
              onClick={handleToggleComplete}
              disabled={isToggling}
              className="flex-1"
              variant={task.completed ? "outline" : "default"}
            >
              {isToggling ? (
                "更新中..."
              ) : task.completed ? (
                "未完了にする"
              ) : (
                "完了にする"
              )}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
