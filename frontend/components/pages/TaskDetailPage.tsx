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
import { useState } from "react";

interface TaskDetailPageProps {
  task: Task;
}

export default function TaskDetailPage({ task }: TaskDetailPageProps) {
  const router = useRouter();
  const [isToggling, setIsToggling] = useState(false);
  const [currentTask, setCurrentTask] = useState<Task>(task);

  // Toggle task completion status
  const handleToggleComplete = async () => {
    try {
      setIsToggling(true);
      const updatedTask = await TaskService.toggleTaskCompletion(currentTask, !currentTask.completed);
      setCurrentTask(updatedTask);
    } catch (err) {
      console.error("Failed to toggle task completion:", err);
      // Error handling (show toast notification if needed)
    } finally {
      setIsToggling(false);
    }
  };

  // Handle back button click
  const handleGoBack = () => {
    router.back();
  };

  const expired = isTaskExpired(currentTask);
  const expiryDate = currentTask.expires_at ? fromUnixTime(currentTask.expires_at) : null;

  return (
    <div className="container mx-auto px-6 py-8 max-w-2xl">
      <Card className="w-full">
        <CardHeader className="pb-4">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <CardTitle className={`text-xl font-semibold ${currentTask.completed ? 'line-through text-muted-foreground' : ''}`}>
                {currentTask.title}
              </CardTitle>
              <div className="flex gap-2 mt-3">
                {currentTask.completed && (
                  <Badge variant="secondary" className="text-xs">
                    完了
                  </Badge>
                )}
                {expired && !currentTask.completed && (
                  <Badge variant="destructive" className="text-xs">
                    期限切れ
                  </Badge>
                )}
              </div>
            </div>
          </div>
        </CardHeader>

        <CardContent className="space-y-6">
          {/* Description */}
          {currentTask.description && (
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
                <FileText className="w-4 h-4" />
                説明
              </div>
              <div className="pl-6 text-sm whitespace-pre-wrap">
                {currentTask.description}
              </div>
            </div>
          )}

          {/* Due date */}
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
              <div className={`pl-6 text-sm ${expired && !currentTask.completed ? 'text-red-600 font-medium' : ''}`}>
                {format(expiryDate, 'yyyy年M月d日 HH:mm', { locale: ja })}
                {expired && !currentTask.completed && (
                  <span className="ml-2 text-red-500">(期限切れ)</span>
                )}
              </div>
            </div>
          )}

          {/* Action buttons */}
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
              variant={currentTask.completed ? "outline" : "default"}
            >
              {isToggling ? (
                "更新中..."
              ) : currentTask.completed ? (
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
