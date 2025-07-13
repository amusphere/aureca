import { Task } from "@/types/Task";

/**
 * Sort tasks by expiry date
 * - Tasks with no expiry date go to the end
 * - Tasks with expiry date are sorted by date (earliest first)
 */
export function sortTasksByExpiry(tasks: Task[]): Task[] {
  return tasks.sort((a, b) => {
    // 期限がない場合は最後に
    if (!a.expires_at && !b.expires_at) return 0;
    if (!a.expires_at) return 1;
    if (!b.expires_at) return -1;

    // 期限が近い順（昇順）
    return a.expires_at - b.expires_at;
  });
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
 * Get tasks by completion status
 */
export function filterTasksByCompletion(tasks: Task[], completed: boolean): Task[] {
  return tasks.filter(task => task.completed === completed);
}

/**
 * Format expiry date for display
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
