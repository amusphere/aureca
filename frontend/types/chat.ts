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

/**
 * Extended AI response that includes usage information
 * Used when AI chat responses need to include usage limit data
 */
export interface AIResponseWithUsage extends AIResponse {
  usage?: {
    remainingCount: number;
    dailyLimit: number;
    resetTime: string;
  };
}
