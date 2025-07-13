"use client";

import { Task } from "@/types/Task";
import { TaskService } from "@/utils/taskService";
import { useRouter } from "next/navigation";
import { useCallback, useState } from "react";
import { ErrorState, useErrorHandling } from "./useErrorHandling";

interface UseTaskDetailReturn {
  // State
  currentTask: Task;
  isToggling: boolean;

  // Actions
  toggleComplete: () => Promise<void>;
  editTask: () => void;
  deleteTask: () => void;
  goBack: () => void;

  // Error handling
  error: ErrorState | null;
  clearError: () => void;
}

/**
 * Custom hook for managing task detail page state and actions
 */
export function useTaskDetail(initialTask: Task): UseTaskDetailReturn {
  const router = useRouter();
  const [currentTask, setCurrentTask] = useState<Task>(initialTask);
  const [isToggling, setIsToggling] = useState(false);
  const { error, withErrorHandling, clearError } = useErrorHandling();

  // Toggle task completion status
  const toggleComplete = useCallback(async () => {
    setIsToggling(true);
    try {
      await withErrorHandling(
        async () => {
          const updatedTask = await TaskService.toggleTaskCompletion(
            currentTask,
            !currentTask.completed
          );
          setCurrentTask(updatedTask);
          return updatedTask;
        },
        {
          onError: (error) => {
            console.error("Failed to toggle task completion:", error.message);
          }
        }
      );
    } finally {
      setIsToggling(false);
    }
  }, [currentTask, withErrorHandling]);

  // Navigate to edit page
  const editTask = useCallback(() => {
    // TODO: Implement edit functionality
    console.log("Edit task:", currentTask.uuid);
  }, [currentTask.uuid]);

  // Delete task
  const deleteTask = useCallback(() => {
    // TODO: Implement delete functionality
    console.log("Delete task:", currentTask.uuid);
  }, [currentTask.uuid]);

  // Navigate back
  const goBack = useCallback(() => {
    router.back();
  }, [router]);

  return {
    // State
    currentTask,
    isToggling,

    // Actions
    toggleComplete,
    editTask,
    deleteTask,
    goBack,

    // Error handling
    error,
    clearError,
  };
}
