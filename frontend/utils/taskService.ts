import { CreateTaskRequest, Task, UpdateTaskRequest } from "@/types/Task";

export interface ApiResponse<T> {
  data?: T;
  error?: {
    message: string;
    status: number;
  };
}

export class TaskService {
  private static readonly BASE_URL = '/api/tasks';

  /**
   * Get all tasks with optional filtering
   */
  static async getTasks(completed?: boolean): Promise<Task[]> {
    const queryParams = new URLSearchParams();
    if (completed !== undefined) {
      queryParams.append('completed', completed.toString());
    }

    const url = queryParams.toString()
      ? `${this.BASE_URL}?${queryParams.toString()}`
      : this.BASE_URL;

    const response = await fetch(url);

    if (!response.ok) {
      throw new Error(`Failed to fetch tasks: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Create a new task
   */
  static async createTask(taskData: CreateTaskRequest): Promise<Task> {
    const response = await fetch(this.BASE_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(taskData),
    });

    if (!response.ok) {
      throw new Error(`Failed to create task: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Update an existing task
   */
  static async updateTask(taskUuid: string, taskData: UpdateTaskRequest): Promise<Task> {
    const response = await fetch(`${this.BASE_URL}/${taskUuid}`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(taskData),
    });

    if (!response.ok) {
      throw new Error(`Failed to update task: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Delete a task
   */
  static async deleteTask(taskUuid: string): Promise<void> {
    const response = await fetch(`${this.BASE_URL}/${taskUuid}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      throw new Error(`Failed to delete task: ${response.statusText}`);
    }
  }

  /**
   * Toggle task completion status
   */
  static async toggleTaskCompletion(task: Task, completed: boolean): Promise<Task> {
    return this.updateTask(task.uuid, {
      title: task.title,
      description: task.description,
      completed: completed,
      expires_at: task.expires_at,
    });
  }
}
