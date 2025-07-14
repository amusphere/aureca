"use client";

import { TaskSource } from "@/types/Task";
import { Calendar, Clipboard, ExternalLink, Github, Mail, MessageSquare } from "lucide-react";
import { MarkdownContent } from "../chat/MarkdownContent";

interface TaskSourcesProps {
  sources: TaskSource[];
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
  if (!sources || sources.length === 0) {
    return null;
  }

  return (
    <div className="space-y-1">
      <div className="text-xs font-medium text-muted-foreground mb-2">
        関連情報
      </div>
      <div className="space-y-1">
        {sources.map((source) => (
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
          </div>
        ))}
      </div>
    </div>
  );
}
