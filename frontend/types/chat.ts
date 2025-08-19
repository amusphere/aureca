// Legacy message interface for backward compatibility
export interface Message {
  id: string;
  content: string;
  isUser: boolean;
  timestamp: Date;
}

// New chat thread and message interfaces based on API specification
export interface ChatThread {
  uuid: string;
  title: string | null;
  created_at: number;
  updated_at: number;
  message_count: number;
}

export interface ChatMessage {
  uuid: string;
  role: 'user' | 'assistant';
  content: string;
  created_at: number;
}

export interface PaginationInfo {
  page: number;
  per_page: number;
  total_messages: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface ChatThreadWithMessages {
  thread: ChatThread;
  messages: ChatMessage[];
  pagination: PaginationInfo;
}

// API Request/Response types
export interface CreateChatThreadRequest {
  title?: string;
}

export interface SendMessageRequest {
  content: string;
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

// Utility type for converting ChatMessage to legacy Message format
export interface MessageWithThread extends Message {
  threadUuid?: string;
}
