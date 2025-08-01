"use client";

import { Badge } from "@/components/components/ui/badge";
import { Button } from "@/components/components/ui/button";
import { Card, CardContent } from "@/components/components/ui/card";
import { Task } from "@/types/Task";
import { formatTaskExpiry, getTaskStatus } from "@/utils/taskUtils";
import { CalendarIcon, CheckIcon, ClockIcon, EditIcon, TrashIcon } from "lucide-react";
import { useRouter } from "next/navigation";
import { TaskPriorityBadge, isPriorityHigh } from "./TaskPriorityBadge";

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
  const handleCardClick = (e: React.MouseEvent | React.KeyboardEvent) => {
    // ボタンクリック時は詳細ページに遷移しない
    if ((e.target as HTMLElement).closest('button')) {
      return;
    }
    router.push(`/tasks/${task.uuid}`);
  };

  return (
    <Card
      role="article"
      aria-label={`タスク: ${task.title}${task.completed ? ' (完了済み)' : ''}${isExpired && !task.completed ? ' (期限切れ)' : ''}`}
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          handleCardClick(e);
        }
      }}
      className={`
        cursor-pointer group transition-all duration-300 ease-out hover-lift focus-ring
        ${task.completed ? 'opacity-75' : ''}
        ${isExpired && !task.completed ? 'border-destructive/50' : ''}
        ${isCompleting ? 'animate-[completion_0.6s_ease-out_forwards]' : ''}
        ${isUncompleting ? 'animate-[uncompletion_0.6s_ease-out_forwards]' : ''}
        ${isPriorityHigh(task.priority) && !task.completed ? 'border-destructive/30 bg-destructive/5' : ''}
        hover:shadow-lg hover:border-border/80 hover:scale-[1.01]
        active:scale-[0.99] active:shadow-sm
        animate-fade-in-up
      `}
      onClick={handleCardClick}
    >
      <CardContent className="p-3 sm:p-4 @container">
        <div className="flex items-start @sm:items-center gap-2 @sm:gap-3">
          <Button
            variant="ghost"
            size="icon-xs"
            aria-label={task.completed ? `タスク「${task.title}」を未完了にする` : `タスク「${task.title}」を完了にする`}
            aria-pressed={task.completed}
            className={`
              rounded-full border shrink-0 mt-0.5 sm:mt-0 transition-all duration-300 ease-out
              hover:scale-110 active:scale-95 hover:shadow-sm
              ${task.completed
                ? 'bg-success/20 text-success border-success/30 hover:bg-success/30 hover:border-success/40 animate-gentle-bounce'
                : 'border-border/60 hover:border-success/40 hover:bg-success/10'
              }
            `}
            onClick={() => onToggleComplete?.(task.uuid, !task.completed)}
          >
            {task.completed && <CheckIcon className="w-3 h-3 transition-transform duration-200" />}
            <span className="sr-only">
              {task.completed ? '完了済み' : '未完了'}
            </span>
          </Button>

          <div className="flex-1 min-w-0">
            <div className="flex flex-col gap-1 sm:gap-2 mb-2 sm:mb-1">
              {/* タイトル行 */}
              <div className="flex items-start sm:items-center gap-2">
                <h3 className={`
                  text-sm font-medium leading-tight break-words flex-1 min-w-0
                  ${task.completed
                    ? 'line-through text-muted-foreground'
                    : 'text-foreground'
                  }
                `}>
                  {task.title}
                </h3>

                {/* タイトルのすぐ右に優先度バッジを配置（PC・モバイル共通） */}
                <div className="flex items-center shrink-0">
                  <TaskPriorityBadge
                    priority={task.priority}
                    size="sm"
                    showIcon={true}
                    showLabel={false}
                  />
                </div>
              </div>

              {/* デスクトップ用のバッジ行 */}
              <div className="hidden sm:flex items-center gap-1 flex-wrap shrink-0">
                {task.completed && (
                  <Badge variant="status-completed" size="sm">
                    完了
                  </Badge>
                )}
                {isExpired && !task.completed && (
                  <Badge variant="destructive" size="sm">
                    期限切れ
                  </Badge>
                )}
              </div>

              {/* モバイル用のステータスバッジ行 */}
              <div className="flex items-center gap-1 flex-wrap sm:hidden">
                {task.completed && (
                  <Badge variant="status-completed" size="sm">
                    完了
                  </Badge>
                )}
                {isExpired && !task.completed && (
                  <Badge variant="destructive" size="sm">
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
            <div className="flex flex-col sm:flex-row gap-1 opacity-0 group-hover:opacity-100 transition-all duration-300 ease-out shrink-0">
              {onEdit && (
                <Button
                  variant="ghost"
                  size="icon-sm"
                  aria-label={`タスク「${task.title}」を編集`}
                  className="hover:bg-accent/80 hover:text-accent-foreground transition-all duration-300 ease-out hover:scale-110 active:scale-95 hover:shadow-sm"
                  onClick={() => onEdit(task)}
                >
                  <EditIcon className="w-3.5 h-3.5 transition-transform duration-200" />
                  <span className="sr-only">編集</span>
                </Button>
              )}
              {onDelete && (
                <Button
                  variant="ghost"
                  size="icon-sm"
                  aria-label={`タスク「${task.title}」を削除`}
                  className="hover:bg-destructive/10 hover:text-destructive transition-all duration-300 ease-out hover:scale-110 active:scale-95 hover:shadow-sm"
                  onClick={() => onDelete(task.uuid)}
                >
                  <TrashIcon className="w-3.5 h-3.5 transition-transform duration-200" />
                  <span className="sr-only">削除</span>
                </Button>
              )}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
