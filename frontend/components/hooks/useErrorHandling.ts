"use client";

import { useCallback, useState } from "react";

export interface ErrorState {
  message: string;
  type: 'network' | 'validation' | 'server' | 'unknown';
  retryable: boolean;
}

interface UseErrorHandlingReturn {
  error: ErrorState | null;
  setError: (error: string | Error | ErrorState) => void;
  clearError: () => void;
  withErrorHandling: <T>(
    operation: () => Promise<T>,
    options?: {
      retryable?: boolean;
      onError?: (error: ErrorState) => void;
    }
  ) => Promise<T | null>;
}

/**
 * Custom hook for unified error handling across the application
 */
export function useErrorHandling(): UseErrorHandlingReturn {
  const [error, setErrorState] = useState<ErrorState | null>(null);

  const setError = useCallback((error: string | Error | ErrorState) => {
    if (typeof error === 'string') {
      setErrorState({
        message: error,
        type: 'unknown',
        retryable: true
      });
    } else if (error instanceof Error) {
      // Determine error type based on error message
      let type: ErrorState['type'] = 'unknown';
      let retryable = true;

      if (error.message.includes('fetch') || error.message.includes('network')) {
        type = 'network';
      } else if (error.message.includes('validation') || error.message.includes('required')) {
        type = 'validation';
        retryable = false;
      } else if (error.message.includes('server') || error.message.includes('500')) {
        type = 'server';
      }

      setErrorState({
        message: error.message,
        type,
        retryable
      });
    } else {
      setErrorState(error);
    }
  }, []);

  const clearError = useCallback(() => {
    setErrorState(null);
  }, []);

  const withErrorHandling = useCallback(async <T,>(
    operation: () => Promise<T>,
    options?: {
      retryable?: boolean;
      onError?: (error: ErrorState) => void;
    }
  ): Promise<T | null> => {
    try {
      const result = await operation();
      clearError(); // Clear any previous errors on success
      return result;
    } catch (err) {
      const errorState: ErrorState = {
        message: err instanceof Error ? err.message : 'An unknown error occurred',
        type: 'unknown',
        retryable: options?.retryable ?? true
      };

      setErrorState(errorState);
      options?.onError?.(errorState);

      return null;
    }
  }, [clearError]);

  return {
    error,
    setError,
    clearError,
    withErrorHandling
  };
}
