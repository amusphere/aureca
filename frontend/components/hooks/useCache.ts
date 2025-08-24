import { useQuery, useQueryClient } from '@tanstack/react-query';

/**
 * Example hook demonstrating React Query caching functionality
 * This can be used as a reference for implementing cached API calls
 */
export function useCache() {
  const queryClient = useQueryClient();

  // Example query with 5-minute cache as specified in requirements
  const { data, isLoading, error } = useQuery({
    queryKey: ['cache-example'],
    queryFn: async () => {
      // This is just an example - replace with actual API call
      return { timestamp: Date.now(), message: 'Cached data' };
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
  });

  const invalidateCache = () => {
    queryClient.invalidateQueries({ queryKey: ['cache-example'] });
  };

  const clearCache = () => {
    queryClient.removeQueries({ queryKey: ['cache-example'] });
  };

  return {
    data,
    isLoading,
    error,
    invalidateCache,
    clearCache,
  };
}