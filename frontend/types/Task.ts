export interface Task {
  uuid: string;
  title: string;
  description?: string;
  completed: boolean;
  expires_at?: number;
}

export interface CreateTaskRequest {
  title: string;
  description?: string;
  expires_at?: number;
}

export interface UpdateTaskRequest {
  title?: string;
  description?: string;
  completed?: boolean;
  expires_at?: number;
}
