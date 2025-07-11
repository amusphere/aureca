"use client";

import { Badge } from "@/components/components/ui/badge";
import { Button } from "@/components/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/components/ui/card";
import { Task } from "@/types/Task";
import { format, fromUnixTime } from "date-fns";
import { ja } from "date-fns/locale";
import { CalendarIcon, CheckIcon, ClockIcon } from "lucide-react";

interface TaskCardProps {
  task: Task;
  onToggleComplete?: (taskId: string, completed: boolean) => void;
  onEdit?: (task: Task) => void;
  onDelete?: (taskId: string) => void;
}

export function TaskCard({ task, onToggleComplete, onEdit, onDelete }: TaskCardProps) {
  const isExpired = task.expires_at ? Date.now() / 1000 > task.expires_at : false;
  const expiryDate = task.expires_at ? fromUnixTime(task.expires_at) : null;

  return (
    <Card className={`transition-all duration-200 ${task.completed ? 'opacity-60' : ''} ${isExpired && !task.completed ? 'border-red-200 bg-red-50' : ''}`}>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-3 flex-1">
            <Button
              variant="ghost"
              size="sm"
              className={`p-1 h-6 w-6 rounded ${task.completed ? 'bg-green-100 text-green-600' : 'hover:bg-gray-100'}`}
              onClick={() => onToggleComplete?.(task.uuid, !task.completed)}
            >
              {task.completed && <CheckIcon className="w-4 h-4" />}
            </Button>
            <div className="flex-1">
              <CardTitle className={`text-lg ${task.completed ? 'line-through text-muted-foreground' : ''}`}>
                {task.title}
              </CardTitle>
              {task.description && (
                <CardDescription className="mt-1">
                  {task.description}
                </CardDescription>
              )}
            </div>
          </div>
          <div className="flex gap-1">
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
      </CardHeader>

      {(expiryDate || onEdit || onDelete) && (
        <CardContent className="pt-0">
          <div className="flex items-center justify-between">
            {expiryDate && (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                {isExpired ? (
                  <ClockIcon className="w-4 h-4 text-red-500" />
                ) : (
                  <CalendarIcon className="w-4 h-4" />
                )}
                <span className={isExpired && !task.completed ? 'text-red-600' : ''}>
                  期限: {format(expiryDate, 'yyyy年MM月dd日 HH:mm', { locale: ja })}
                </span>
              </div>
            )}

            {(onEdit || onDelete) && (
              <div className="flex gap-2">
                {onEdit && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => onEdit(task)}
                  >
                    編集
                  </Button>
                )}
                {onDelete && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => onDelete(task.uuid)}
                    className="text-red-600 hover:text-red-700"
                  >
                    削除
                  </Button>
                )}
              </div>
            )}
          </div>
        </CardContent>
      )}
    </Card>
  );
}
