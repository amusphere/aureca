export interface TaskSource {
  uuid: string;
  source_type: string;
  source_url?: string;
  source_id?: string;
  title?: string;
  content?: string;
  extra_data?: string;
  created_at?: number;
  updated_at?: number;
}

export interface Task {
  uuid: string;
  title: string;
  description?: string;
  completed: boolean;
  expires_at?: number;
  sources?: TaskSource[];
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
