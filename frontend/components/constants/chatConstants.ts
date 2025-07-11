export const CHAT_STYLES = {
  container: "w-full h-full flex flex-col bg-gray-50",
  errorAlert: "flex-shrink-0 p-4",
  errorContent: "bg-red-100 border-l-4 border-red-500 text-red-700 p-4 rounded-md",
  messagesContainer: "flex-1 overflow-y-auto px-4 py-2 min-h-0",
  emptyState: "flex flex-col items-center justify-center h-full text-center text-gray-500",
  emptyStateTitle: "text-4xl font-bold text-gray-800 mb-2",
  messagesList: "space-y-4 pb-4",
  inputContainer: "flex-shrink-0 bg-white/70 backdrop-blur-sm border-t border-gray-200/50",
} as const;

export const CHAT_CONSTANTS = {
  emptyStateTitle: "Aureca AI",
  emptyStateDescription: "AIアシスタントに話しかけてみましょう。",
  errorTitle: "エラー",
  fallbackErrorMessage: "不明なエラーが発生しました",
  completionMessage: "処理が完了しました。",
  apiErrorMessage: "エラーが発生しました。",
} as const;
