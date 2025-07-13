"use client";

import { CreateTaskRequest, Task } from "@/types/Task";
import { useCallback, useEffect, useState } from "react";
import { sortTasksByExpiry, sortCompletedTasks } from "@/utils/taskUtils";
import { TaskService } from "@/utils/taskService";

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

  // Fetch tasks from API using TaskService
  const fetchTasks = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Fetch active and completed tasks using TaskService
      const [activeData, completedData] = await Promise.all([
        TaskService.getTasks(false),
        TaskService.getTasks(true)
      ]);

      const sortedActiveTasks = sortTasksByExpiry(activeData);
      setActiveTasks(sortedActiveTasks);
      setCompletedTasks(completedData);

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to fetch tasks";
      setError(errorMessage);
      console.error("Error fetching tasks:", err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Create new task using TaskService
  const createTask = useCallback(async (taskData: CreateTaskRequest) => {
    setError(null);

    try {
      await TaskService.createTask(taskData);
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

      // API call to update task using TaskService
      const updatedTask = await TaskService.toggleTaskCompletion(task, completed);

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
  }, [activeTasks, completedTasks, fetchTasks]);

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
