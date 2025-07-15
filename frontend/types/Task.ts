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

// ソースタイプ関連の型定義
export interface SourceTypeConfig {
  icon: React.ComponentType<{ className?: string }>;
  displayName: string;
  color?: string;
}

export type SourceTypeKey =
  | "email"
  | "calendar"
  | "slack"
  | "teams"
  | "discord"
  | "github_issue"
  | "github_pr"
  | "jira"
  | "trello"
  | "asana"
  | "notion"
  | "linear"
  | "clickup"
  | "other";
