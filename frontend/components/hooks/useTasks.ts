"use client";

import { CreateTaskRequest, Task } from "@/types/Task";
import { TaskService } from "@/utils/taskService";
import { sortTasksByExpiry } from "@/utils/taskUtils";
import { useCallback, useEffect, useState } from "react";
import { ErrorState, useErrorHandling } from "./useErrorHandling";

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
  error: ErrorState | null;
  clearError: () => void;
}

const ANIMATION_DURATION = 700;

/**
 * Unified hook for task operations with proper error handling
 * Follows AGENTS.md structure - hooks/ directory for custom hooks
 */
export function useTasks(): UseTasksReturn {
  // State management
  const [activeTasks, setActiveTasks] = useState<Task[]>([]);
  const [completedTasks, setCompletedTasks] = useState<Task[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [completingTasks, setCompletingTasks] = useState<Set<string>>(new Set());
  const [uncompletingTasks, setUncompletingTasks] = useState<Set<string>>(new Set());
  
  // Unified error handling
  const { error, withErrorHandling, clearError } = useErrorHandling();

  // Fetch tasks from API using TaskService
  const fetchTasks = useCallback(async () => {
    setIsLoading(true);
    
    try {
      await withErrorHandling(
        async () => {
          const [activeData, completedData] = await Promise.all([
            TaskService.getTasks(false),
            TaskService.getTasks(true)
          ]);

          const sortedActiveTasks = sortTasksByExpiry(activeData);
          setActiveTasks(sortedActiveTasks);
          setCompletedTasks(completedData);
        },
        {
          onError: (error) => {
            console.error("Error fetching tasks:", error.message);
          }
        }
      );
    } finally {
      setIsLoading(false);
    }
  }, [withErrorHandling]);

  // Create new task using TaskService with unified error handling
  const createTask = useCallback(async (taskData: CreateTaskRequest) => {
    await withErrorHandling(
      async () => {
        await TaskService.createTask(taskData);
        await fetchTasks();
      },
      {
        onError: (error) => {
          console.error("Failed to create task:", error.message);
          throw error; // Re-throw for form error handling
        }
      }
    );
  }, [withErrorHandling, fetchTasks]);

  // Toggle task completion with animation and unified error handling
  const toggleTaskComplete = useCallback(async (taskUuid: string, completed: boolean) => {
    await withErrorHandling(
      async () => {
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
        await TaskService.toggleTaskCompletion(task, completed);

        // Update state after animation
        setTimeout(() => {
          if (completed) {
            // Move from active to completed
            setActiveTasks(prev => prev.filter(t => t.uuid !== taskUuid));
            setCompletedTasks(prev => [{ ...task, completed: true }, ...prev]);
            setCompletingTasks(prev => {
              const newSet = new Set(prev);
              newSet.delete(taskUuid);
              return newSet;
            });
          } else {
            // Move from completed to active
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
      },
      {
        onError: (error) => {
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

          console.error("Failed to update task:", error.message);
          // Refresh data on error
          fetchTasks();
        }
      }
    );
  }, [withErrorHandling, activeTasks, completedTasks, fetchTasks]);

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
