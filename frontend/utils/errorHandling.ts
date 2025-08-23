/**
 * Error handling utilities for user-friendly error messages.
 *
 * This module provides utilities for handling API errors and displaying
 * appropriate user-friendly messages based on error types and codes.
 */

export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, unknown>;
}

export interface ApiErrorResponse {
  error: ApiError;
}

/**
 * Error message mappings for different error codes.
 */
const ERROR_MESSAGES: Record<string, string> = {
  // Stripe errors
  STRIPE_CONFIG_ERROR: "Payment service is temporarily unavailable. Please try again later or contact support.",
  STRIPE_AUTH_ERROR: "Payment service authentication failed. Please contact support.",
  STRIPE_API_ERROR: "Payment service is experiencing issues. Please try again later.",
  STRIPE_CONNECTION_ERROR: "Unable to connect to payment service. Please check your internet connection.",
  STRIPE_CUSTOMER_CREATE_ERROR: "Failed to set up your payment account. Please try again.",
  STRIPE_CUSTOMER_NOT_FOUND: "Payment account not found. Please contact support.",
  STRIPE_INVALID_REQUEST: "Invalid payment request. Please check your information and try again.",
  STRIPE_SIGNATURE_ERROR: "Invalid payment webhook. This request has been rejected for security reasons.",
  STRIPE_WEBHOOK_ERROR: "Payment status update failed. Your subscription status will be updated shortly.",

  // Subscription errors
  SUBSCRIPTION_NOT_FOUND: "Subscription not found. Please check your subscription status.",

  // User errors
  USER_NOT_FOUND: "User account not found. Please check your account status.",

  // Database errors
  DATABASE_ERROR: "A database error occurred. Please try again later.",

  // Validation errors
  VALIDATION_ERROR: "Please check your input and try again.",

  // Rate limiting
  RATE_LIMIT_EXCEEDED: "Too many requests. Please wait a moment before trying again.",

  // Generic errors
  INTERNAL_SERVER_ERROR: "An unexpected error occurred. Please try again later.",
  NETWORK_ERROR: "Network error. Please check your internet connection and try again.",
  TIMEOUT_ERROR: "Request timed out. Please try again.",
};

/**
 * Extract error information from an API response.
 *
 * @param error - The error object from the API response
 * @returns Extracted error information
 */
export function extractApiError(error: unknown): ApiError {
  // Handle different error formats
  if (
    error &&
    typeof error === "object" &&
    "response" in error &&
    error.response &&
    typeof error.response === "object" &&
    "data" in error.response &&
    error.response.data &&
    typeof error.response.data === "object" &&
    "error" in error.response.data
  ) {
    // Standard API error format
    return error.response.data.error as ApiError;
  } else if (error && typeof error === "object" && "error" in error) {
    // Direct error object
    return error.error as ApiError;
  } else if (error && typeof error === "object" && "message" in error && typeof error.message === "string") {
    // Simple error with message
    return {
      code: "UNKNOWN_ERROR",
      message: error.message,
    };
  } else {
    // Fallback for unknown error formats
    return {
      code: "UNKNOWN_ERROR",
      message: "An unknown error occurred",
    };
  }
}

/**
 * Get a user-friendly error message for an error code.
 *
 * @param errorCode - The error code from the API
 * @param fallbackMessage - Optional fallback message if code is not found
 * @returns User-friendly error message
 */
export function getUserFriendlyMessage(errorCode: string, fallbackMessage?: string): string {
  return ERROR_MESSAGES[errorCode] || fallbackMessage || "An unexpected error occurred. Please try again.";
}

/**
 * Format an API error for display to the user.
 *
 * @param error - The error object from the API
 * @returns Formatted error message
 */
export function formatErrorMessage(error: unknown): string {
  const apiError = extractApiError(error);

  // Use the message from the API if it's user-friendly, otherwise use our mapping
  if (apiError.message && !apiError.message.includes("Exception") && !apiError.message.includes("Error:")) {
    return apiError.message;
  }

  return getUserFriendlyMessage(apiError.code, apiError.message);
}

/**
 * Check if an error is retryable.
 *
 * @param error - The error object
 * @returns True if the error is retryable
 */
export function isRetryableError(error: unknown): boolean {
  const apiError = extractApiError(error);

  const retryableCodes = [
    "STRIPE_CONNECTION_ERROR",
    "STRIPE_API_ERROR",
    "DATABASE_ERROR",
    "NETWORK_ERROR",
    "TIMEOUT_ERROR",
    "INTERNAL_SERVER_ERROR",
  ];

  return retryableCodes.includes(apiError.code);
}

/**
 * Check if an error requires user action.
 *
 * @param error - The error object
 * @returns True if the error requires user action
 */
export function requiresUserAction(error: unknown): boolean {
  const apiError = extractApiError(error);

  const userActionCodes = [
    "STRIPE_INVALID_REQUEST",
    "VALIDATION_ERROR",
    "SUBSCRIPTION_NOT_FOUND",
    "USER_NOT_FOUND",
  ];

  return userActionCodes.includes(apiError.code);
}

/**
 * Check if an error is a security-related error.
 *
 * @param error - The error object
 * @returns True if the error is security-related
 */
export function isSecurityError(error: unknown): boolean {
  const apiError = extractApiError(error);

  const securityCodes = [
    "STRIPE_SIGNATURE_ERROR",
    "STRIPE_AUTH_ERROR",
  ];

  return securityCodes.includes(apiError.code);
}

/**
 * Get suggested actions for an error.
 *
 * @param error - The error object
 * @returns Array of suggested actions
 */
export function getSuggestedActions(error: unknown): string[] {
  const apiError = extractApiError(error);

  const actionMap: Record<string, string[]> = {
    STRIPE_CONNECTION_ERROR: [
      "Check your internet connection",
      "Try again in a few moments",
      "Contact support if the problem persists",
    ],
    STRIPE_INVALID_REQUEST: [
      "Check your payment information",
      "Ensure all required fields are filled",
      "Try using a different payment method",
    ],
    VALIDATION_ERROR: [
      "Check all form fields for errors",
      "Ensure required information is provided",
      "Correct any highlighted issues",
    ],
    RATE_LIMIT_EXCEEDED: [
      "Wait a few minutes before trying again",
      "Avoid making too many requests quickly",
    ],
    SUBSCRIPTION_NOT_FOUND: [
      "Check your subscription status",
      "Contact support for assistance",
    ],
    NETWORK_ERROR: [
      "Check your internet connection",
      "Try refreshing the page",
      "Try again in a few moments",
    ],
  };

  return actionMap[apiError.code] || [
    "Try again in a few moments",
    "Contact support if the problem persists",
  ];
}

/**
 * Log an error for debugging purposes.
 *
 * @param error - The error object
 * @param context - Additional context about where the error occurred
 */
export function logError(error: unknown, context?: string): void {
  const apiError = extractApiError(error);

  console.error("API Error:", {
    code: apiError.code,
    message: apiError.message,
    details: apiError.details,
    context,
    timestamp: new Date().toISOString(),
  });
}

/**
 * Create a standardized error object for consistent handling.
 *
 * @param code - Error code
 * @param message - Error message
 * @param details - Additional error details
 * @returns Standardized error object
 */
export function createError(code: string, message: string, details?: Record<string, unknown>): ApiError {
  return {
    code,
    message,
    details,
  };
}
