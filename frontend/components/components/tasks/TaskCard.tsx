"use client";

import { Badge } from "@/components/components/ui/badge";
import { Button } from "@/components/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/components/ui/card";
import { Task } from "@/types/Task";
import { CalendarIcon, CheckIcon, ClockIcon } from "lucide-react";
import { useRouter } from "next/navigation";
import { getTaskStatus, formatTaskExpiry } from "@/utils/taskUtils";

interface TaskCardProps {
  task: Task;
  isCompleting?: boolean;
  isUncompleting?: boolean;
  onToggleComplete?: (taskId: string, completed: boolean) => void;
  onEdit?: (task: Task) => void;
  onDelete?: (taskId: string) => void;
}

export function TaskCard({ task, isCompleting = false, isUncompleting = false, onToggleComplete, onEdit, onDelete }: TaskCardProps) {
  const router = useRouter();

  // ユーティリティ関数を使用して状態を取得
  const { isExpired } = getTaskStatus(task);
  const formattedExpiry = formatTaskExpiry(task, 'M/d HH:mm');

  // タスク詳細ページへの遷移
  const handleCardClick = (e: React.MouseEvent) => {
    // ボタンクリック時は詳細ページに遷移しない
    if ((e.target as HTMLElement).closest('button')) {
      return;
    }
    router.push(`/tasks/${task.uuid}`);
  };

  return (
    <Card
      className={`w-full transition-all duration-700 ease-out cursor-pointer hover:shadow-md ${task.completed ? 'opacity-60' : ''} ${isExpired && !task.completed ? 'border-red-200 bg-red-50' : ''} ${isCompleting ? 'transform scale-110 opacity-0 translate-x-8 rotate-3 bg-green-100 border-green-300 shadow-lg' : ''
        } ${isUncompleting ? 'transform scale-110 opacity-0 -translate-x-8 -rotate-3 bg-blue-100 border-blue-300 shadow-lg' : ''
        }`}
      onClick={handleCardClick}
    >
      <CardHeader className="p-3 pb-2">
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-3 flex-1">
            <Button
              variant="ghost"
              size="sm"
              className={`p-1 h-6 w-6 rounded-full border-2 transition-all duration-200 ${task.completed
                ? 'bg-green-100 text-green-600 border-green-300'
                : 'border-gray-300 hover:border-green-400 hover:bg-green-50'
                }`}
              onClick={() => onToggleComplete?.(task.uuid, !task.completed)}
            >
              {task.completed && <CheckIcon className="w-4 h-4" />}
            </Button>
            <div className="flex-1 min-w-0">
              <CardTitle className={`text-sm font-medium ${task.completed ? 'line-through text-muted-foreground' : ''}`}>
                {task.title}
              </CardTitle>
              {task.description && (
                <CardDescription className="mt-1 text-xs">
                  {task.description}
                </CardDescription>
              )}
              {formattedExpiry && (
                <div className="flex items-center gap-1 mt-1">
                  {isExpired ? (
                    <ClockIcon className="w-3 h-3 text-red-500" />
                  ) : (
                    <CalendarIcon className="w-3 h-3 text-muted-foreground" />
                  )}
                  <span className={`text-xs ${isExpired && !task.completed ? 'text-red-600 font-medium' : 'text-muted-foreground'}`}>
                    {formattedExpiry}
                  </span>
                </div>
              )}
            </div>
          </div>
          <div className="flex gap-1 ml-2">
            {task.completed && (
              <Badge variant="secondary" className="text-xs px-1 py-0">
                完了
              </Badge>
            )}
            {isExpired && !task.completed && (
              <Badge variant="destructive" className="text-xs px-1 py-0">
                期限切れ
              </Badge>
            )}
          </div>
        </div>
      </CardHeader>

      {(onEdit || onDelete) && (
        <CardContent className="p-3 pt-0">
          <div className="flex justify-end gap-1">
            {onEdit && (
              <Button
                variant="outline"
                size="sm"
                className="h-7 px-2 text-xs"
                onClick={() => onEdit(task)}
              >
                編集
              </Button>
            )}
            {onDelete && (
              <Button
                variant="outline"
                size="sm"
                className="h-7 px-2 text-xs text-red-600 hover:text-red-700"
                onClick={() => onDelete(task.uuid)}
              >
                削除
              </Button>
            )}
          </div>
        </CardContent>
      )}
    </Card>
  );
}
