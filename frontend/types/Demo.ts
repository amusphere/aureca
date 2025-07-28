export interface DemoTask {
  id: string;
  title: string;
  description?: string;
  completed: boolean;
  expires_at?: number;
  created_at: number;
  source_type: 'demo';
}

export interface DemoSession {
  id: string;
  tasks: DemoTask[];
  created_at: number;
  expires_at: number | null;
  limitations: {
    max_tasks: number | null;
    max_duration: number | null;
    current_task_count: number;
  };
}

export interface DemoLimitation {
  type: 'task_limit' | 'time_limit' | 'feature_disabled';
  message: string;
  action?: 'upgrade' | 'register';
}

export interface CreateDemoTaskRequest {
  title: string;
  description?: string;
  expires_at?: number;
}

export interface UpdateDemoTaskRequest {
  title?: string;
  description?: string;
  completed?: boolean;
  expires_at?: number;
}