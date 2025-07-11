"use server";

import { CreateTaskRequest, Task, UpdateTaskRequest } from "@/types/Task";
import { apiDelete, apiGet, apiPatch, apiPost, ApiResponse } from "@/utils/api";

/**
 * タスク一覧を取得
 */
export async function getTasks(
  completed: boolean = false,
  expires_at?: number
): Promise<ApiResponse<Task[]>> {
  const params = new URLSearchParams();
  params.append("completed", completed.toString());
  if (expires_at !== undefined) {
    params.append("expires_at", expires_at.toString());
  }

  const endpoint = `/tasks?${params.toString()}`;
  return apiGet<Task[]>(endpoint);
}

/**
 * 指定したIDのタスクを取得
 */
export async function getTask(taskId: number): Promise<ApiResponse<Task>> {
  return apiGet<Task>(`/tasks/${taskId}`);
}

/**
 * 新しいタスクを作成
 */
export async function createTask(task: CreateTaskRequest): Promise<ApiResponse<Task>> {
  return apiPost<Task>("/tasks", task);
}

/**
 * タスクを更新
 */
export async function updateTask(
  taskId: number,
  task: UpdateTaskRequest
): Promise<ApiResponse<Task>> {
  return apiPatch<Task>(`/tasks/${taskId}`, task);
}

/**
 * タスクを完了済みにマーク
 */
export async function completeTask(taskId: number): Promise<ApiResponse<Task>> {
  return apiPatch<Task>(`/tasks/${taskId}/complete`);
}

/**
 * タスクを未完了にマーク
 */
export async function incompleteTask(taskId: number): Promise<ApiResponse<Task>> {
  return apiPatch<Task>(`/tasks/${taskId}/incomplete`);
}

/**
 * タスクを削除
 */
export async function deleteTask(taskId: number): Promise<ApiResponse<{ message: string }>> {
  return apiDelete<{ message: string }>(`/tasks/${taskId}`);
}
