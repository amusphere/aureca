"use client";

import { CreateTaskRequest, Task } from "@/types/Task";
import { useCallback, useEffect, useState } from "react";

interface UseTasksReturn {
  // State
  activeTasks: Task[];
  completedTasks: Task[];
  isLoading: boolean;

  // Animation states
  completingTasks: Set<string>;
  uncompletingTasks: Set<string>;

  // Actions
  fetchTasks: () => Promise<void>;
  createTask: (taskData: CreateTaskRequest) => Promise<void>;
  toggleTaskComplete: (taskUuid: string, completed: boolean) => Promise<void>;

  // Error handling
  error: string | null;
  clearError: () => void;
}

const ANIMATION_DURATION = 700;

export function useTasks(): UseTasksReturn {
  // State management
  const [activeTasks, setActiveTasks] = useState<Task[]>([]);
  const [completedTasks, setCompletedTasks] = useState<Task[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [completingTasks, setCompletingTasks] = useState<Set<string>>(new Set());
  const [uncompletingTasks, setUncompletingTasks] = useState<Set<string>>(new Set());
  const [error, setError] = useState<string | null>(null);

  // Sort tasks by expiry date (expired first, then by date, then no expiry)
  const sortTasksByExpiry = useCallback((tasks: Task[]) => {
    return tasks.sort((a, b) => {
      // 期限がない場合は最後に
      if (!a.expires_at && !b.expires_at) return 0;
      if (!a.expires_at) return 1;
      if (!b.expires_at) return -1;

      // 期限が近い順（昇順）
      return a.expires_at - b.expires_at;
    });
  }, []);

  // Fetch tasks from API
  const fetchTasks = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Fetch active tasks
      const activeResponse = await fetch("/api/tasks?completed=false");
      if (!activeResponse.ok) throw new Error("Failed to fetch active tasks");

      const activeData = await activeResponse.json();
      const sortedActiveTasks = sortTasksByExpiry(activeData);
      setActiveTasks(sortedActiveTasks);

      // Fetch completed tasks
      const completedResponse = await fetch("/api/tasks?completed=true");
      if (!completedResponse.ok) throw new Error("Failed to fetch completed tasks");

      const completedData = await completedResponse.json();
      setCompletedTasks(completedData);

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to fetch tasks";
      setError(errorMessage);
      console.error("Error fetching tasks:", err);
    } finally {
      setIsLoading(false);
    }
  }, [sortTasksByExpiry]);

  // Create new task
  const createTask = useCallback(async (taskData: CreateTaskRequest) => {
    setError(null);

    try {
      const response = await fetch("/api/tasks", {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(taskData),
      });

      if (!response.ok) throw new Error('Failed to create task');

      // Refresh tasks after creation
      await fetchTasks();

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to create task";
      setError(errorMessage);
      throw err; // Re-throw for form error handling
    }
  }, [fetchTasks]);

  // Toggle task completion with animation
  const toggleTaskComplete = useCallback(async (taskUuid: string, completed: boolean) => {
    setError(null);

    try {
      // Find the task
      const allTasks = [...activeTasks, ...completedTasks];
      const task = allTasks.find(t => t.uuid === taskUuid);
      if (!task) throw new Error("Task not found");

      // Start animation
      if (completed) {
        setCompletingTasks(prev => new Set([...prev, taskUuid]));
      } else {
        setUncompletingTasks(prev => new Set([...prev, taskUuid]));
      }

      // API call to update task
      const response = await fetch(`/api/tasks/${taskUuid}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          uuid: task.uuid,
          title: task.title,
          description: task.description,
          completed: completed,
          expires_at: task.expires_at,
        }),
      });

      if (!response.ok) throw new Error('Failed to update task');

      // Update state after animation
      setTimeout(() => {
        if (completed) {
          // Move from active to completed (at the beginning)
          setActiveTasks(prev => prev.filter(t => t.uuid !== taskUuid));
          setCompletedTasks(prev => [{ ...task, completed: true }, ...prev]);
          setCompletingTasks(prev => {
            const newSet = new Set(prev);
            newSet.delete(taskUuid);
            return newSet;
          });
        } else {
          // Move from completed to active (sorted by expiry)
          setCompletedTasks(prev => prev.filter(t => t.uuid !== taskUuid));
          setActiveTasks(prev => {
            const updatedTask = { ...task, completed: false };
            const newActiveTasks = [...prev, updatedTask];
            return sortTasksByExpiry(newActiveTasks);
          });
          setUncompletingTasks(prev => {
            const newSet = new Set(prev);
            newSet.delete(taskUuid);
            return newSet;
          });
        }
      }, ANIMATION_DURATION);

    } catch (err) {
      // Clean up animation states on error
      setCompletingTasks(prev => {
        const newSet = new Set(prev);
        newSet.delete(taskUuid);
        return newSet;
      });
      setUncompletingTasks(prev => {
        const newSet = new Set(prev);
        newSet.delete(taskUuid);
        return newSet;
      });

      const errorMessage = err instanceof Error ? err.message : "Failed to update task";
      setError(errorMessage);

      // Refresh data on error
      await fetchTasks();
    }
  }, [activeTasks, completedTasks, sortTasksByExpiry, fetchTasks]);

  // Clear error
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // Initial data fetch
  useEffect(() => {
    fetchTasks();
  }, [fetchTasks]);

  return {
    // State
    activeTasks,
    completedTasks,
    isLoading,

    // Animation states
    completingTasks,
    uncompletingTasks,

    // Actions
    fetchTasks,
    createTask,
    toggleTaskComplete,

    // Error handling
    error,
    clearError,
  };
}
