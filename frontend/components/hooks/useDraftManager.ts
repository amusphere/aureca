"use client";

import { EmailDraft } from "@/types/EmailDraft";
import { TaskSource } from "@/types/Task";
import { useCallback, useEffect, useState } from "react";
import { useErrorHandling } from "./useErrorHandling";

interface GeneratedDraftInfo {
  draft: EmailDraft;
  message?: string;
  isExisting?: boolean;
}

interface UseDraftManagerReturn {
  generatedDrafts: Record<string, GeneratedDraftInfo>;
  isGeneratingDraft: boolean;
  isLoadingDraft: boolean;
  isLoadingDraftForSource: (sourceUuid: string) => boolean;
  generateDraft: (source: TaskSource) => Promise<void>;
  getExistingDraft: (source: TaskSource) => Promise<void>;
  error: ReturnType<typeof useErrorHandling>['error'];
  clearError: () => void;
}

/**
 * Custom hook for managing email draft generation and retrieval
 * Follows DRY, KISS principles with proper error handling
 */
export function useDraftManager(sources: TaskSource[]): UseDraftManagerReturn {
  const [isGeneratingDraft, setIsGeneratingDraft] = useState(false);
  const [isLoadingDraft, setIsLoadingDraft] = useState(false);
  const [loadingDraftSources, setLoadingDraftSources] = useState<Set<string>>(new Set());
  const [generatedDrafts, setGeneratedDrafts] = useState<Record<string, GeneratedDraftInfo>>({});
  const [checkedSources, setCheckedSources] = useState<Set<string>>(new Set());

  const { error, withErrorHandling, clearError } = useErrorHandling();

  const isLoadingDraftForSource = useCallback((sourceUuid: string): boolean => {
    return loadingDraftSources.has(sourceUuid);
  }, [loadingDraftSources]);

  const getExistingDraft = useCallback(async (source: TaskSource) => {
    if (source.source_type !== "email") return;

    setLoadingDraftSources(prev => new Set([...prev, source.uuid]));
    setIsLoadingDraft(true);
    try {
      await withErrorHandling(
        async () => {
          const response = await fetch(`/api/mail/drafts/${source.uuid}`);

          if (response.ok) {
            const draft: EmailDraft = await response.json();
            setGeneratedDrafts(prev => ({
              ...prev,
              [source.uuid]: {
                draft,
                message: "既存のドラフトが見つかりました",
                isExisting: true
              }
            }));
          } else if (response.status === 404) {
            // 404は正常なケース（ドラフトが存在しない）
            console.log('No existing draft found for this email');
          } else {
            throw new Error(`Failed to fetch draft: ${response.statusText}`);
          }
        },
        {
          retryable: true,
          onError: (error) => console.error('Error fetching existing draft:', error.message)
        }
      );
    } finally {
      setLoadingDraftSources(prev => {
        const newSet = new Set([...prev]);
        newSet.delete(source.uuid);
        return newSet;
      });
      setIsLoadingDraft(false);
    }
  }, [withErrorHandling]);

  const generateDraft = useCallback(async (source: TaskSource) => {
    if (source.source_type !== "email") return;

    setIsGeneratingDraft(true);
    try {
      await withErrorHandling(
        async () => {
          const response = await fetch(`/api/ai/generate-email-reply-draft/${source.uuid}`, {
            method: 'POST',
          });

          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }

          const data: EmailDraft = await response.json();

          setGeneratedDrafts(prev => ({
            ...prev,
            [source.uuid]: {
              draft: data,
              message: "メール下書きが生成されました",
              isExisting: false
            }
          }));
        },
        {
          retryable: true,
          onError: (error) => console.error('Error generating draft:', error.message)
        }
      );
    } finally {
      setIsGeneratingDraft(false);
    }
  }, [withErrorHandling]);

  // 初期表示時に既存ドラフトを取得
  useEffect(() => {
    const emailSources = sources.filter(source => source.source_type === "email");
    emailSources.forEach(source => {
      if (!checkedSources.has(source.uuid) && !generatedDrafts[source.uuid]) {
        setCheckedSources(prev => new Set([...prev, source.uuid]));
        getExistingDraft(source);
      }
    });
  }, [sources, getExistingDraft, checkedSources, generatedDrafts]);

  return {
    generatedDrafts,
    isGeneratingDraft,
    isLoadingDraft,
    isLoadingDraftForSource,
    generateDraft,
    getExistingDraft,
    error,
    clearError
  };
}
