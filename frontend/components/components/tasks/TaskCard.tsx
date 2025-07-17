"use client";

import { Badge } from "@/components/components/ui/badge";
import { Button } from "@/components/components/ui/button";
import { Card, CardContent } from "@/components/components/ui/card";
import { Task } from "@/types/Task";
import { formatTaskExpiry, getTaskStatus } from "@/utils/taskUtils";
import { CalendarIcon, CheckIcon, ClockIcon, EditIcon, TrashIcon } from "lucide-react";
import { useRouter } from "next/navigation";

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
      className={`
        cursor-pointer group transition-all duration-200
        ${task.completed ? 'opacity-75' : ''}
        ${isExpired && !task.completed ? 'border-destructive/50' : ''}
        ${isCompleting ? 'animate-[completion_0.6s_ease-out_forwards]' : ''}
        ${isUncompleting ? 'animate-[uncompletion_0.6s_ease-out_forwards]' : ''}
        hover:shadow-md
      `}
      onClick={handleCardClick}
    >
      <CardContent className="p-3 sm:p-4">
        <div className="flex items-start sm:items-center gap-3">
          <Button
            variant="ghost"
            size="sm"
            className={`
              p-0 h-6 w-6 rounded-full border shrink-0 mt-0.5 sm:mt-0
              ${task.completed
                ? 'bg-green-100 text-green-600 border-green-300'
                : 'border-gray-300 hover:border-green-400'
              }
            `}
            onClick={() => onToggleComplete?.(task.uuid, !task.completed)}
          >
            {task.completed && <CheckIcon className="w-3 h-3" />}
          </Button>

          <div className="flex-1 min-w-0">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1 sm:gap-2 mb-2 sm:mb-1">
              <h3 className={`
                text-sm font-medium leading-tight break-words sm:truncate flex-1
                ${task.completed
                  ? 'line-through text-muted-foreground'
                  : 'text-foreground'
                }
              `}>
                {task.title}
              </h3>

              <div className="flex items-center gap-1 flex-wrap shrink-0">
                {task.completed && (
                  <Badge variant="secondary" className="text-xs">
                    完了
                  </Badge>
                )}
                {isExpired && !task.completed && (
                  <Badge variant="destructive" className="text-xs">
                    期限切れ
                  </Badge>
                )}
              </div>
            </div>

            <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4 text-xs text-muted-foreground">
              {task.description && (
                <span className="break-words sm:truncate sm:flex-1 max-w-full overflow-hidden">
                  {task.description}
                </span>
              )}
              {formattedExpiry && (
                <div className="flex items-center gap-1 shrink-0">
                  {isExpired ? (
                    <ClockIcon className="w-3 h-3 text-destructive" />
                  ) : (
                    <CalendarIcon className="w-3 h-3" />
                  )}
                  <span className={`whitespace-nowrap ${isExpired && !task.completed ? 'text-destructive' : ''}`}>
                    {formattedExpiry}
                  </span>
                </div>
              )}
            </div>
          </div>

          {(onEdit || onDelete) && (
            <div className="flex flex-col sm:flex-row gap-1 opacity-0 group-hover:opacity-100 transition-opacity shrink-0">
              {onEdit && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-7 w-7 sm:h-8 sm:w-8 p-0"
                  onClick={() => onEdit(task)}
                >
                  <EditIcon className="w-3.5 h-3.5 sm:w-4 sm:h-4" />
                </Button>
              )}
              {onDelete && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-7 w-7 sm:h-8 sm:w-8 p-0 hover:text-destructive"
                  onClick={() => onDelete(task.uuid)}
                >
                  <TrashIcon className="w-3.5 h-3.5 sm:w-4 sm:h-4" />
                </Button>
              )}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
