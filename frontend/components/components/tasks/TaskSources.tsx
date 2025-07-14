"use client";

import { Button } from "@/components/components/ui/button";
import { TaskSource } from "@/types/Task";
import { Calendar, Clipboard, ExternalLink, Github, Mail, MessageSquare, PenTool } from "lucide-react";
import { useState } from "react";
import { MarkdownContent } from "../chat/MarkdownContent";

interface TaskSourcesProps {
  sources: TaskSource[];
}

interface EmailDraft {
  subject: string;
  body: string;
}

interface EmailDraftResponse {
  success: boolean;
  message: string;
  draft: EmailDraft;
}

interface GeneratedDraftInfo {
  draft: EmailDraft;
  message: string;
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
      return <Github className="w-4 h-4" />;
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
  const [generatedDrafts, setGeneratedDrafts] = useState<Record<string, GeneratedDraftInfo>>({});

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

      const data: EmailDraftResponse = await response.json();

      if (data.success) {
        setGeneratedDrafts(prev => ({
          ...prev,
          [source.uuid]: {
            draft: data.draft,
            message: data.message
          }
        }));
      } else {
        console.error('Draft generation failed:', data.message);
      }
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
              {source.source_type === "email" && !hasGeneratedDraft && (
                <div className="mt-2">
                  <Button
                    onClick={() => generateEmailDraft(source)}
                    disabled={isGeneratingDraft}
                    variant="outline"
                    size="sm"
                    className="h-7 text-xs px-2"
                  >
                    <PenTool className="w-3 h-3 mr-1" />
                    {isGeneratingDraft ? "生成中..." : "返信下書き生成"}
                  </Button>
                </div>
              )}

              {/* 生成された下書きを表示 */}
              {hasGeneratedDraft && (
                <div className="mt-2 p-2 bg-gray-50 rounded-md border space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium text-gray-700">生成された返信下書き</span>
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
                    <div className="text-xs text-green-600 bg-green-50 p-1 rounded">
                      {hasGeneratedDraft.message}
                    </div>
                  )}
                  <div className="space-y-1">
                    <div className="text-xs">
                      <strong>件名:</strong> {hasGeneratedDraft.draft.subject}
                    </div>
                    <div className="text-xs">
                      <strong>本文:</strong>
                      <div className="mt-1 text-muted-foreground whitespace-pre-wrap line-clamp-4">
                        {hasGeneratedDraft.draft.body}
                      </div>
                    </div>
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
