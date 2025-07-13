import { Task } from "@/types/Task";
import { format, fromUnixTime } from "date-fns";
import { ja } from "date-fns/locale";

/**
 * Sort tasks by expiry date
 * - Tasks with no expiry date go to the end
 * - Tasks with expiry date are sorted by date (earliest first)
 */
export function sortTasksByExpiry(tasks: Task[]): Task[] {
  return tasks.sort((a, b) => {
    // Tasks without expiry date go last
    if (!a.expires_at && !b.expires_at) return 0;
    if (!a.expires_at) return 1;
    if (!b.expires_at) return -1;

    // Sort by expiry date ascending (closest first)
    return a.expires_at - b.expires_at;
  });
}

/**
 * Sort completed tasks by title alphabetically
 */
export function sortCompletedTasks(tasks: Task[]): Task[] {
  return tasks.sort((a, b) => a.title.localeCompare(b.title, 'ja'));
}

/**
 * Check if a task is expired
 */
export function isTaskExpired(task: Task): boolean {
  if (!task.expires_at) return false;
  const currentTimeInSeconds = Math.floor(Date.now() / 1000);
  return currentTimeInSeconds > task.expires_at;
}

/**
 * Format task expiry date for display
 */
export function formatTaskExpiry(task: Task, formatString: string = 'yyyy年M月d日 HH:mm'): string | null {
  if (!task.expires_at) return null;
  const expiryDate = fromUnixTime(task.expires_at);
  return format(expiryDate, formatString, { locale: ja });
}

/**
 * Get task status for display
 */
export function getTaskStatus(task: Task): {
  isExpired: boolean;
  isCompleted: boolean;
  statusText: string;
  variant: 'default' | 'secondary' | 'destructive';
} {
  const isExpired = isTaskExpired(task);
  const isCompleted = task.completed;

  if (isCompleted) {
    return {
      isExpired,
      isCompleted,
      statusText: '完了',
      variant: 'secondary'
    };
  }

  if (isExpired) {
    return {
      isExpired,
      isCompleted,
      statusText: '期限切れ',
      variant: 'destructive'
    };
  }

  return {
    isExpired,
    isCompleted,
    statusText: 'アクティブ',
    variant: 'default'
  };
}

/**
 * Get tasks by completion status
 */
export function filterTasksByCompletion(tasks: Task[], completed: boolean): Task[] {
  return tasks.filter(task => task.completed === completed);
}

/**
 * Format expiry date for display (legacy - use formatTaskExpiry instead)
 * @deprecated Use formatTaskExpiry instead
 */
export function formatExpiryDate(expiryTimestamp: number): string {
  const date = new Date(expiryTimestamp * 1000);
  return date.toLocaleDateString('ja-JP', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
}
