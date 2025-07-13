import { Task } from "@/types/Task";
import { fromUnixTime } from "date-fns";

/**
 * Unified task utilities following AGENTS.md structure
 * Consolidated task-related utility functions for better maintainability
 */

// ===== SORTING UTILITIES =====

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

// ===== FILTERING UTILITIES =====

/**
 * Get tasks by completion status
 */
export function filterTasksByCompletion(tasks: Task[], completed: boolean): Task[] {
  return tasks.filter(task => task.completed === completed);
}

/**
 * Filter expired tasks
 */
export function getExpiredTasks(tasks: Task[]): Task[] {
  const currentTimeInSeconds = Math.floor(Date.now() / 1000);
  return tasks.filter(task =>
    task.expires_at && currentTimeInSeconds > task.expires_at
  );
}

/**
 * Filter tasks expiring soon (within specified hours)
 */
export function getTasksExpiringSoon(tasks: Task[], withinHours: number = 24): Task[] {
  const currentTimeInSeconds = Math.floor(Date.now() / 1000);
  const thresholdTime = currentTimeInSeconds + (withinHours * 60 * 60);

  return tasks.filter(task =>
    task.expires_at &&
    task.expires_at > currentTimeInSeconds &&
    task.expires_at <= thresholdTime
  );
}

// ===== STATUS UTILITIES =====

/**
 * Check if a task is expired
 */
export function isTaskExpired(task: Task): boolean {
  if (!task.expires_at) return false;
  const currentTimeInSeconds = Math.floor(Date.now() / 1000);
  return currentTimeInSeconds > task.expires_at;
}

/**
 * Check if a task is expiring soon
 */
export function isTaskExpiringSoon(task: Task, withinHours: number = 24): boolean {
  if (!task.expires_at) return false;
  const currentTimeInSeconds = Math.floor(Date.now() / 1000);
  const thresholdTime = currentTimeInSeconds + (withinHours * 60 * 60);
  return task.expires_at > currentTimeInSeconds && task.expires_at <= thresholdTime;
}

/**
 * Get comprehensive task status for display
 */
export function getTaskStatus(task: Task): {
  isExpired: boolean;
  isExpiringSoon: boolean;
  isCompleted: boolean;
  statusText: string;
  variant: 'default' | 'secondary' | 'destructive' | 'warning';
} {
  const isExpired = isTaskExpired(task);
  const isExpiringSoon = isTaskExpiringSoon(task);
  const isCompleted = task.completed;

  if (isCompleted) {
    return {
      isExpired,
      isExpiringSoon,
      isCompleted,
      statusText: '完了',
      variant: 'secondary'
    };
  }

  if (isExpired) {
    return {
      isExpired,
      isExpiringSoon,
      isCompleted,
      statusText: '期限切れ',
      variant: 'destructive'
    };
  }

  if (isExpiringSoon) {
    return {
      isExpired,
      isExpiringSoon,
      isCompleted,
      statusText: 'まもなく期限',
      variant: 'warning'
    };
  }

  return {
    isExpired,
    isExpiringSoon,
    isCompleted,
    statusText: 'アクティブ',
    variant: 'default'
  };
}

// ===== FORMATTING UTILITIES =====

/**
 * Format task expiry date for display
 * Uses toLocaleDateString for SSR compatibility
 */
export function formatTaskExpiry(task: Task, formatString: string = 'yyyy年M月d日 HH:mm'): string | null {
  if (!task.expires_at) return null;
  const expiryDate = fromUnixTime(task.expires_at);

  // Use toLocaleDateString for SSR compatibility
  if (formatString === 'M/d HH:mm') {
    return expiryDate.toLocaleDateString('ja-JP', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      timeZone: 'Asia/Tokyo'
    });
  }

  // Default format
  return expiryDate.toLocaleDateString('ja-JP', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    timeZone: 'Asia/Tokyo'
  });
}

/**
 * Get relative time description for task expiry
 */
export function getTaskExpiryRelativeTime(task: Task): string | null {
  if (!task.expires_at) return null;

  const currentTimeInSeconds = Math.floor(Date.now() / 1000);
  const diffInSeconds = task.expires_at - currentTimeInSeconds;

  if (diffInSeconds < 0) {
    return '期限切れ';
  }

  const diffInMinutes = Math.floor(diffInSeconds / 60);
  const diffInHours = Math.floor(diffInMinutes / 60);
  const diffInDays = Math.floor(diffInHours / 24);

  if (diffInDays > 0) {
    return `${diffInDays}日後`;
  } else if (diffInHours > 0) {
    return `${diffInHours}時間後`;
  } else if (diffInMinutes > 0) {
    return `${diffInMinutes}分後`;
  } else {
    return 'まもなく';
  }
}

// ===== STATISTICS UTILITIES =====

/**
 * Get task statistics
 */
export function getTaskStatistics(tasks: Task[]) {
  const total = tasks.length;
  const completed = tasks.filter(task => task.completed).length;
  const active = total - completed;
  const expired = getExpiredTasks(tasks.filter(task => !task.completed)).length;
  const expiringSoon = getTasksExpiringSoon(tasks.filter(task => !task.completed)).length;

  return {
    total,
    completed,
    active,
    expired,
    expiringSoon,
    completionRate: total > 0 ? Math.round((completed / total) * 100) : 0
  };
}

// ===== LEGACY FUNCTIONS (DEPRECATED) =====

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
