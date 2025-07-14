"use client";

import { Button } from "@/components/components/ui/button";
import { EmailDraft } from "@/types/EmailDraft";
import { TaskSource } from "@/types/Task";
import { Calendar, Clipboard, ExternalLink, GitBranch, Mail, MessageSquare, PenTool } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { MarkdownContent } from "../chat/MarkdownContent";

interface TaskSourcesProps {
  sources: TaskSource[];
}

interface GeneratedDraftInfo {
  draft: EmailDraft;
  message?: string;
  isExisting?: boolean; // 既存のドラフトかどうか
}

const getSourceIcon = (sourceType: string) => {
  switch (sourceType) {
    case "email":
      return <Mail className="w-4 h-4" />;
    case "calendar":
      return <Calendar className="w-4 h-4" />;
    case "slack":
    case "teams":
    case "discord":
      return <MessageSquare className="w-4 h-4" />;
    case "github_issue":
    case "github_pr":
      return <GitBranch className="w-4 h-4" />;
    default:
      return <Clipboard className="w-4 h-4" />;
  }
};

const getSourceDisplayName = (sourceType: string): string => {
  const displayNames: Record<string, string> = {
    email: "メール",
    calendar: "カレンダー",
    slack: "Slack",
    teams: "Teams",
    discord: "Discord",
    github_issue: "GitHub Issue",
    github_pr: "GitHub PR",
    jira: "Jira",
    trello: "Trello",
    asana: "Asana",
    notion: "Notion",
    linear: "Linear",
    clickup: "ClickUp",
    other: "その他"
  };
  return displayNames[sourceType] || sourceType;
};

export function TaskSources({ sources }: TaskSourcesProps) {
  const [isGeneratingDraft, setIsGeneratingDraft] = useState(false);
  const [isLoadingDraft, setIsLoadingDraft] = useState(false);
  const [generatedDrafts, setGeneratedDrafts] = useState<Record<string, GeneratedDraftInfo>>({});
  const [checkedSources, setCheckedSources] = useState<Set<string>>(new Set());

  // 既存のドラフトを取得する関数
  const getExistingDraft = useCallback(async (source: TaskSource) => {
    if (source.source_type !== "email") return;

    setIsLoadingDraft(true);
    try {
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
        // ドラフトが見つからない場合は何もしない
        console.log('No existing draft found for this email');
      } else {
        console.error('Error fetching existing draft:', response.statusText);
      }
    } catch (error) {
      console.error('Error fetching existing draft:', error);
    } finally {
      setIsLoadingDraft(false);
    }
  }, []);

  // メールソースの既存ドラフトを初期表示時に取得
  useEffect(() => {
    const emailSources = sources.filter(source => source.source_type === "email");
    emailSources.forEach(source => {
      if (!checkedSources.has(source.uuid) && !generatedDrafts[source.uuid]) {
        setCheckedSources(prev => new Set([...prev, source.uuid]));
        getExistingDraft(source);
      }
    });
  }, [sources, getExistingDraft, checkedSources, generatedDrafts]);

  if (!sources || sources.length === 0) {
    return null;
  }

  const generateEmailDraft = async (source: TaskSource) => {
    if (source.source_type !== "email") return;

    setIsGeneratingDraft(true);
    try {
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
    } catch (error) {
      console.error('Error generating draft:', error);
    } finally {
      setIsGeneratingDraft(false);
    }
  };

  return (
    <div className="space-y-1">
      <div className="text-xs font-medium text-muted-foreground mb-2">
        関連情報
      </div>
      <div className="space-y-1">
        {sources.map((source) => {
          const hasGeneratedDraft = generatedDrafts[source.uuid];

          return (
            <div key={source.uuid} className="py-1">
              <div className="flex items-center justify-between gap-2 mb-1">
                <div className="flex items-center gap-1">
                  {getSourceIcon(source.source_type)}
                  <span className="text-xs text-muted-foreground">
                    {getSourceDisplayName(source.source_type)}
                  </span>
                </div>
                {source.source_url && (
                  <a
                    href={source.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:text-blue-800 transition-colors flex-shrink-0"
                    aria-label="外部リンクを開く"
                  >
                    <ExternalLink className="w-3 h-3" />
                  </a>
                )}
              </div>

              {source.title && (
                <div className="font-medium text-xs text-gray-900 break-words line-clamp-1 mb-1">
                  {source.title}
                </div>
              )}

              {source.content && (
                <div className="text-xs text-muted-foreground prose prose-xs max-w-none overflow-hidden line-clamp-2">
                  <MarkdownContent content={source.content} className="break-words" />
                </div>
              )}

              {/* メール返信ドラフト生成ボタン */}
              {source.source_type === "email" && (
                <div className="mt-2">
                  {!hasGeneratedDraft ? (
                    <Button
                      onClick={() => generateEmailDraft(source)}
                      disabled={isGeneratingDraft || isLoadingDraft}
                      variant="outline"
                      size="sm"
                      className="h-7 text-xs px-2"
                    >
                      <PenTool className="w-3 h-3 mr-1" />
                      {isGeneratingDraft ? "生成中..." : isLoadingDraft ? "確認中..." : "返信下書き生成"}
                    </Button>
                  ) : hasGeneratedDraft.isExisting && (
                    <Button
                      onClick={() => generateEmailDraft(source)}
                      disabled={isGeneratingDraft}
                      variant="outline"
                      size="sm"
                      className="h-7 text-xs px-2"
                    >
                      <PenTool className="w-3 h-3 mr-1" />
                      {isGeneratingDraft ? "生成中..." : "新しい下書きを生成"}
                    </Button>
                  )}
                </div>
              )}

              {/* 生成された下書きを表示 */}
              {hasGeneratedDraft && (
                <div className="mt-2 p-2 bg-gray-50 rounded-md border space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium text-gray-700">
                      {hasGeneratedDraft.isExisting ? "既存の返信下書き" : "生成された返信下書き"}
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
                  {hasGeneratedDraft.message && (
                    <div className={`text-xs p-1 rounded ${hasGeneratedDraft.isExisting
                        ? "text-blue-600 bg-blue-50"
                        : "text-green-600 bg-green-50"
                      }`}>
                      {hasGeneratedDraft.message}
                    </div>
                  )}
                  <div className="space-y-1">
                    {hasGeneratedDraft.draft.to && (
                      <div className="text-xs">
                        <strong>宛先:</strong> {hasGeneratedDraft.draft.to}
                      </div>
                    )}
                    {hasGeneratedDraft.draft.subject && (
                      <div className="text-xs">
                        <strong>件名:</strong> {hasGeneratedDraft.draft.subject}
                      </div>
                    )}
                    {hasGeneratedDraft.draft.body && (
                      <div className="text-xs">
                        <strong>本文:</strong>
                        <div className="mt-1 text-muted-foreground whitespace-pre-wrap line-clamp-4">
                          <MarkdownContent content={hasGeneratedDraft.draft.body} />
                        </div>
                      </div>
                    )}
                    {hasGeneratedDraft.draft.snippet && (
                      <div className="text-xs text-gray-500">
                        <strong>プレビュー:</strong> {hasGeneratedDraft.draft.snippet}
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
