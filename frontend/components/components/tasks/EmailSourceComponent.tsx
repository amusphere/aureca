import { Button } from "@/components/components/ui/button";
import { EmailDraft } from "@/types/EmailDraft";
import { TaskSource } from "@/types/Task";
import { PenTool, Trash2 } from "lucide-react";
import { MarkdownContent } from "../chat/MarkdownContent";

interface EmailDraftInfo {
  draft: EmailDraft;
  message?: string;
  isExisting?: boolean;
}

interface EmailSourceComponentProps {
  source: TaskSource;
  draftInfo?: EmailDraftInfo;
  onGenerateDraft: (source: TaskSource) => void;
  onDeleteDraft: (source: TaskSource) => void;
  isGeneratingDraft: boolean;
  isLoadingDraft: boolean;
  isDeletingDraft?: boolean;
}

export function EmailSourceComponent({
  source,
  draftInfo,
  onGenerateDraft,
  onDeleteDraft,
  isGeneratingDraft,
  isLoadingDraft,
  isDeletingDraft = false
}: EmailSourceComponentProps) {
  const renderDraftButton = () => {
    // ドラフト情報がない場合（初期状態または確認中）
    if (!draftInfo) {
      const isCheckingDraft = isLoadingDraft;
      const isGenerating = isGeneratingDraft;

      return (
        <Button
          onClick={() => onGenerateDraft(source)}
          disabled={isGenerating || isCheckingDraft}
          variant="outline"
          size="sm"
          className="h-7 text-xs px-2"
        >
          <PenTool className="w-3 h-3 mr-1" />
          {isGenerating ? "生成中..." : isCheckingDraft ? "確認中..." : "返信下書き生成"}
        </Button>
      );
    }

    // ドラフトが存在する場合（既存または新規生成）
    const handleDeleteAndRegenerate = async () => {
      if (isGeneratingDraft || isDeletingDraft) return; // 処理中は何もしない

      try {
        await onDeleteDraft(source);
        await onGenerateDraft(source);
      } catch (error) {
        // エラーハンドリングは上位コンポーネントで処理
      }
    };

    const isProcessing = isGeneratingDraft || isDeletingDraft;

    return (
      <div className="flex gap-1">
        <Button
          onClick={handleDeleteAndRegenerate}
          disabled={isProcessing}
          variant="outline"
          size="sm"
          className="h-7 text-xs px-2"
        >
          <PenTool className="w-3 h-3 mr-1" />
          {isProcessing ? "処理中..." : "再生成"}
        </Button>
        <Button
          onClick={() => onDeleteDraft(source)}
          disabled={isProcessing}
          variant="outline"
          size="sm"
          className="h-7 text-xs px-2 text-red-600 hover:text-red-700 hover:bg-red-50"
        >
          <Trash2 className="w-3 h-3" />
        </Button>
      </div>
    );

    return null;
  };

  const renderDraftDisplay = () => {
    if (!draftInfo) return null;

    return (
      <div className="mt-2 p-2 bg-gray-50 rounded-md border space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium text-gray-700">
            {draftInfo.isExisting ? "既存の返信下書き" : "生成された返信下書き"}
          </span>
          {source.source_url && (
            <a
              href={source.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-blue-600 hover:text-blue-800 underline"
            >
              メールを開く
            </a>
          )}
        </div>

        {draftInfo.message && (
          <div className={`text-xs p-1 rounded ${draftInfo.isExisting
            ? "text-blue-600 bg-blue-50"
            : "text-green-600 bg-green-50"
            }`}>
            {draftInfo.message}
          </div>
        )}

        <div className="space-y-1">
          {draftInfo.draft.to && (
            <div className="text-xs">
              <strong>宛先:</strong> {draftInfo.draft.to}
            </div>
          )}
          {draftInfo.draft.subject && (
            <div className="text-xs">
              <strong>件名:</strong> {draftInfo.draft.subject}
            </div>
          )}
          {draftInfo.draft.body && (
            <div className="text-xs">
              <strong>本文:</strong>
              <div className="mt-1 text-muted-foreground whitespace-pre-wrap line-clamp-4">
                <MarkdownContent content={draftInfo.draft.body} />
              </div>
            </div>
          )}
          {draftInfo.draft.snippet && (
            <div className="text-xs text-gray-500">
              <strong>プレビュー:</strong> {draftInfo.draft.snippet}
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <>
      <div className="mt-2">
        {renderDraftButton()}
      </div>
      {renderDraftDisplay()}
    </>
  );
}
