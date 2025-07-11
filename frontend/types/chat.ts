export interface Message {
  id: string;
  content: string;
  isUser: boolean;
  timestamp: Date;
}

export interface AIResponse {
  success: boolean;
  operator_response?: Record<string, unknown>;
  execution_results?: Record<string, unknown>[];
  summary?: {
    results_text?: string;
    [key: string]: unknown;
  };
  error?: string;
}
