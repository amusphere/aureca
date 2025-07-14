"use client";

import { TaskSource } from "@/types/Task";
import { useDraftManager } from "../../hooks/useDraftManager";
import { EmailSourceComponent } from "./EmailSourceComponent";
import { SourceHeader } from "./SourceHeader";

interface TaskSourcesProps {
  sources: TaskSource[];
}

export function TaskSources({ sources }: TaskSourcesProps) {
  const {
    generatedDrafts,
    isGeneratingDraft,
    isDeletingDraft,
    isLoadingDraftForSource,
    generateDraft,
    deleteDraft,
    error,
    clearError
  } = useDraftManager(sources);

  if (!sources || sources.length === 0) {
    return null;
  }

  const renderSourceTypeComponent = (source: TaskSource) => {
    const draftInfo = generatedDrafts[source.uuid];
    const isLoadingDraftForThisSource = isLoadingDraftForSource(source.uuid);

    switch (source.source_type) {
      case "email":
        return (
          <EmailSourceComponent
            source={source}
            draftInfo={draftInfo}
            onGenerateDraft={generateDraft}
            onDeleteDraft={deleteDraft}
            isGeneratingDraft={isGeneratingDraft}
            isLoadingDraft={isLoadingDraftForThisSource}
            isDeletingDraft={isDeletingDraft}
          />
        );
      default:
        // デフォルトは何も表示しない（将来的に拡張可能）
        return null;
    }
  };

  return (
    <div className="space-y-1">
      <div className="text-xs font-medium text-muted-foreground mb-2">
        関連情報
      </div>

      {/* Error Display */}
      {error && (
        <div className="p-2 bg-red-50 border border-red-200 rounded-md mb-2">
          <div className="flex items-center justify-between">
            <span className="text-xs text-red-600">{error.message}</span>
            <button
              onClick={clearError}
              className="text-red-400 hover:text-red-600"
              aria-label="エラーを閉じる"
            >
              ×
            </button>
          </div>
        </div>
      )}

      <div className="space-y-1">
        {sources.map((source) => (
          <div key={source.uuid} className="py-1">
            <SourceHeader source={source} />
            {renderSourceTypeComponent(source)}
          </div>
        ))}
      </div>
    </div>
  );
}
