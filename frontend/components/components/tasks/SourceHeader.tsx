import { SourceTypeConfig, SourceTypeKey, TaskSource } from "@/types/Task";
import { Calendar, Clipboard, ExternalLink, GitBranch, Mail, MessageSquare } from "lucide-react";
import { MarkdownContent } from "../chat/MarkdownContent";

const SOURCE_TYPE_CONFIG: Record<SourceTypeKey, SourceTypeConfig> = {
  email: {
    icon: Mail,
    displayName: "メール",
    color: "text-blue-600"
  },
  calendar: {
    icon: Calendar,
    displayName: "カレンダー",
    color: "text-green-600"
  },
  slack: {
    icon: MessageSquare,
    displayName: "Slack",
    color: "text-purple-600"
  },
  teams: {
    icon: MessageSquare,
    displayName: "Teams",
    color: "text-blue-500"
  },
  discord: {
    icon: MessageSquare,
    displayName: "Discord",
    color: "text-indigo-600"
  },
  github_issue: {
    icon: GitBranch,
    displayName: "GitHub Issue",
    color: "text-gray-800"
  },
  github_pr: {
    icon: GitBranch,
    displayName: "GitHub PR",
    color: "text-gray-800"
  },
  jira: {
    icon: Clipboard,
    displayName: "Jira",
    color: "text-blue-700"
  },
  trello: {
    icon: Clipboard,
    displayName: "Trello",
    color: "text-blue-400"
  },
  asana: {
    icon: Clipboard,
    displayName: "Asana",
    color: "text-red-500"
  },
  notion: {
    icon: Clipboard,
    displayName: "Notion",
    color: "text-gray-700"
  },
  linear: {
    icon: Clipboard,
    displayName: "Linear",
    color: "text-purple-500"
  },
  clickup: {
    icon: Clipboard,
    displayName: "ClickUp",
    color: "text-pink-500"
  },
  other: {
    icon: Clipboard,
    displayName: "その他",
    color: "text-gray-500"
  }
};

interface SourceHeaderProps {
  source: TaskSource;
}

export function SourceHeader({ source }: SourceHeaderProps) {
  const config = SOURCE_TYPE_CONFIG[source.source_type as SourceTypeKey] || SOURCE_TYPE_CONFIG.other;
  const IconComponent = config.icon;

  return (
    <>
      <div className="flex items-center justify-between gap-2 mb-1">
        <div className="flex items-center gap-1">
          <IconComponent className={`w-4 h-4 ${config.color || 'text-gray-500'}`} />
          <span className="text-xs text-muted-foreground">
            {config.displayName}
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
    </>
  );
}
