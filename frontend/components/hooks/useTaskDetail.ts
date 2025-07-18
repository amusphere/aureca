"use client";

import { Task, UpdateTaskRequest } from "@/types/Task";
import { TaskService } from "@/utils/taskService";
import { useRouter } from "next/navigation";
import { useCallback, useState } from "react";
import { ErrorState, useErrorHandling } from "./useErrorHandling";

interface UseTaskDetailReturn {
  // State
  currentTask: Task;
  isToggling: boolean;
  isEditing: boolean;

  // Actions
  toggleComplete: () => Promise<void>;
  editTask: () => void;
  updateTask: (taskData: UpdateTaskRequest) => Promise<void>;
  deleteTask: () => void;
  goBack: () => void;
  setIsEditing: (isEditing: boolean) => void;

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
  const [isEditing, setIsEditing] = useState(false);
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
          onError: () => {
            // エラーハンドリングは上位コンポーネントで処理
          }
        }
      );
    } finally {
      setIsToggling(false);
    }
  }, [currentTask, withErrorHandling]);

  // Navigate to edit page
  const editTask = useCallback(() => {
    setIsEditing(true);
  }, []);

  // Update task
  const updateTask = useCallback(async (taskData: UpdateTaskRequest) => {
    try {
      await withErrorHandling(
        async () => {
          const updatedTask = await TaskService.updateTask(currentTask.uuid, taskData);
          setCurrentTask(updatedTask);
          setIsEditing(false);
          return updatedTask;
        },
        {
          onError: () => {
            // エラーハンドリングは上位コンポーネントで処理
          }
        }
      );
    } catch {
      // エラーハンドリングは上位コンポーネントで処理
    }
  }, [currentTask.uuid, withErrorHandling]);

  // Delete task
  const deleteTask = useCallback(async () => {
    const isConfirmed = window.confirm('このタスクを削除しますか？');
    if (!isConfirmed) return;

    try {
      await withErrorHandling(
        async () => {
          await TaskService.deleteTask(currentTask.uuid);
          // タスク削除後、タスク一覧ページに戻る
          router.push('/home');
        },
        {
          onError: () => {
            // エラーハンドリングは上位コンポーネントで処理
          }
        }
      );
    } catch {
      // エラーハンドリングは上位コンポーネントで処理
    }
  }, [currentTask.uuid, withErrorHandling, router]);

  // Navigate back
  const goBack = useCallback(() => {
    router.back();
  }, [router]);

  return {
    // State
    currentTask,
    isToggling,
    isEditing,

    // Actions
    toggleComplete,
    editTask,
    updateTask,
    deleteTask,
    goBack,
    setIsEditing,

    // Error handling
    error,
    clearError,
  };
}
