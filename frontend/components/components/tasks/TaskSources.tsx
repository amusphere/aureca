"use client";

import { Badge } from "@/components/components/ui/badge";
import { Card, CardContent } from "@/components/components/ui/card";
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
    <div className="space-y-2">
      <div className="text-sm font-medium text-muted-foreground">
        関連情報
      </div>
      <div className="pl-6 space-y-3">
        {sources.map((source) => (
          <Card key={source.uuid} className="border-l-4 border-l-blue-500">
            <CardContent className="p-4">
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1 space-y-2">
                  <div className="flex items-center gap-2">
                    {getSourceIcon(source.source_type)}
                    <Badge variant="secondary" className="text-xs">
                      {getSourceDisplayName(source.source_type)}
                    </Badge>
                  </div>

                  {source.title && (
                    <div className="font-medium text-sm">
                      {source.title}
                    </div>
                  )}

                  {source.content && (
                    <div className="text-sm text-muted-foreground">
                      <MarkdownContent content={source.content} />
                    </div>
                  )}
                </div>

                {source.source_url && (
                  <a
                    href={source.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:text-blue-800 transition-colors"
                  >
                    <ExternalLink className="w-4 h-4" />
                  </a>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
