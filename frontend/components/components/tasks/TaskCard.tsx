"use client";

import { Badge } from "@/components/components/ui/badge";
import { Button } from "@/components/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/components/ui/card";
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
        w-full cursor-pointer group relative overflow-hidden
        transition-all duration-300 ease-out
        hover:shadow-lg hover:shadow-primary/8 hover:scale-[1.02] hover:-translate-y-1
        active:scale-[0.98] active:transition-none
        ${task.completed
          ? 'opacity-75 bg-muted/40 border-muted-foreground/25 shadow-sm'
          : 'bg-card border-border shadow-md hover:shadow-xl hover:shadow-primary/12 hover:border-primary/30'
        }
        ${isExpired && !task.completed
          ? 'border-error/60 bg-error/8 shadow-error/15 hover:shadow-error/20 hover:border-error/70'
          : ''
        }
        ${isCompleting
          ? 'animate-[completion_0.6s_ease-out_forwards] transform scale-110 opacity-0 translate-x-8 rotate-3 bg-success/15 border-success/60 shadow-xl shadow-success/25'
          : ''
        }
        ${isUncompleting
          ? 'animate-[uncompletion_0.6s_ease-out_forwards] transform scale-110 opacity-0 -translate-x-8 -rotate-3 bg-info/15 border-info/60 shadow-xl shadow-info/25'
          : ''
        }
        rounded-xl border-2 backdrop-blur-sm
        before:absolute before:inset-0 before:bg-gradient-to-br before:from-white/5 before:to-transparent before:opacity-0 before:transition-opacity before:duration-300
        hover:before:opacity-100
        after:absolute after:inset-0 after:rounded-xl after:ring-1 after:ring-inset after:ring-white/10 after:opacity-0 after:transition-opacity after:duration-300
        hover:after:opacity-100
      `}
      onClick={handleCardClick}
    >
      <CardHeader className="p-4 pb-3">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-start gap-3 flex-1 min-w-0">
            <Button
              variant="ghost"
              size="sm"
              className={`
                p-0 h-9 w-9 rounded-full border-2 shrink-0 relative
                transition-all duration-300 ease-out
                hover:scale-110 active:scale-95
                ${task.completed
                  ? 'bg-success/25 text-success border-success/60 hover:bg-success/35 hover:border-success/80 shadow-md shadow-success/25'
                  : 'border-border/50 hover:border-success/80 hover:bg-success/20 hover:shadow-lg hover:shadow-success/15'
                }
                before:absolute before:inset-0 before:rounded-full before:bg-gradient-to-br before:from-white/25 before:to-transparent before:opacity-0 before:transition-opacity before:duration-200
                hover:before:opacity-100
                after:absolute after:inset-0 after:rounded-full after:ring-1 after:ring-inset after:ring-white/20 after:opacity-0 after:transition-opacity after:duration-200
                hover:after:opacity-100
              `}
              onClick={() => onToggleComplete?.(task.uuid, !task.completed)}
            >
              {task.completed && <CheckIcon className="w-4 h-4 drop-shadow-sm" />}
            </Button>
            <div className="flex-1 min-w-0 space-y-1">
              <CardTitle className={`
                text-sm font-semibold leading-tight
                transition-all duration-200
                ${task.completed
                  ? 'line-through text-muted-foreground/70'
                  : 'text-card-foreground group-hover:text-primary'
                }
              `}>
                {task.title}
              </CardTitle>
              {task.description && (
                <CardDescription className="text-xs leading-relaxed text-muted-foreground/80">
                  {task.description}
                </CardDescription>
              )}
              {formattedExpiry && (
                <div className="flex items-center gap-1.5 mt-2">
                  {isExpired ? (
                    <ClockIcon className="w-3.5 h-3.5 text-error shrink-0" />
                  ) : (
                    <CalendarIcon className="w-3.5 h-3.5 text-muted-foreground/60 shrink-0" />
                  )}
                  <span className={`
                    text-xs font-medium
                    ${isExpired && !task.completed
                      ? 'text-error'
                      : 'text-muted-foreground/70'
                    }
                  `}>
                    {formattedExpiry}
                  </span>
                </div>
              )}
            </div>
          </div>
          <div className="flex flex-col gap-1.5 shrink-0">
            {task.completed && (
              <Badge
                variant="secondary"
                className="text-xs px-2.5 py-1 bg-success/15 text-success border-success/30 font-semibold rounded-full shadow-sm shadow-success/10 transition-all duration-200 hover:bg-success/20 hover:shadow-md hover:shadow-success/15"
              >
                完了
              </Badge>
            )}
            {isExpired && !task.completed && (
              <Badge
                variant="destructive"
                className="text-xs px-2.5 py-1 bg-error/15 text-error border-error/40 font-semibold rounded-full animate-pulse shadow-sm shadow-error/15 transition-all duration-200 hover:bg-error/20 hover:shadow-md hover:shadow-error/20"
              >
                期限切れ
              </Badge>
            )}
          </div>
        </div>
      </CardHeader>

      {(onEdit || onDelete) && (
        <CardContent className="px-4 pb-4 pt-0">
          <div className="flex justify-end gap-2 opacity-0 group-hover:opacity-100 transition-all duration-300 ease-out">
            {onEdit && (
              <Button
                variant="ghost"
                size="sm"
                className="
                  h-9 w-9 p-0 rounded-lg relative
                  hover:bg-accent/80 hover:text-accent-foreground
                  transition-all duration-300 ease-out
                  hover:scale-110 active:scale-95
                  hover:shadow-md hover:shadow-accent/20
                  before:absolute before:inset-0 before:rounded-lg before:bg-gradient-to-br before:from-white/20 before:to-transparent before:opacity-0 before:transition-opacity before:duration-200
                  hover:before:opacity-100
                "
                onClick={() => onEdit(task)}
              >
                <EditIcon className="w-4 h-4 text-muted-foreground transition-colors duration-200 hover:text-foreground" />
              </Button>
            )}
            {onDelete && (
              <Button
                variant="ghost"
                size="sm"
                className="
                  h-9 w-9 p-0 rounded-lg relative
                  hover:bg-error/15 hover:text-error
                  transition-all duration-300 ease-out
                  hover:scale-110 active:scale-95
                  hover:shadow-md hover:shadow-error/20
                  before:absolute before:inset-0 before:rounded-lg before:bg-gradient-to-br before:from-white/20 before:to-transparent before:opacity-0 before:transition-opacity before:duration-200
                  hover:before:opacity-100
                "
                onClick={() => onDelete(task.uuid)}
              >
                <TrashIcon className="w-4 h-4 text-muted-foreground transition-colors duration-200 hover:text-error" />
              </Button>
            )}
          </div>
        </CardContent>
      )}
    </Card>
  );
}
