import { Badge } from "@/components/components/ui/badge";
import { cn } from "@/components/lib/utils";
import { TaskPriority } from "@/types/Task";
import { AlertCircle, AlertTriangle, Circle } from "lucide-react";

interface TaskPriorityBadgeProps {
  priority?: TaskPriority;
  size?: "xs" | "sm" | "default" | "lg" | "xl";
  showIcon?: boolean;
  showLabel?: boolean;
  className?: string;
}

// 優先度別の設定
const PRIORITY_CONFIG = {
  1: {
    variant: "priority-high" as const,
    icon: AlertTriangle,
    label: "高",
    ariaLabel: "高優先度",
  },
  2: {
    variant: "priority-medium" as const,
    icon: AlertCircle,
    label: "中",
    ariaLabel: "中優先度",
  },
  3: {
    variant: "priority-low" as const,
    icon: Circle,
    label: "低",
    ariaLabel: "低優先度",
  },
} as const;

export function TaskPriorityBadge({
  priority,
  size = "default",
  showIcon = true,
  showLabel = true,
  className,
}: TaskPriorityBadgeProps) {
  // 優先度が設定されていない場合は何も表示しない
  if (!priority) {
    return null;
  }

  const config = PRIORITY_CONFIG[priority];
  const Icon = config.icon;

  return (
    <Badge
      variant={config.variant}
      size={size}
      className={cn("transition-all duration-300 ease-out", className)}
      aria-label={config.ariaLabel}
      role="status"
    >
      {showIcon && (
        <Icon
          className={cn(
            "transition-transform duration-200",
            // サイズに応じたアイコンサイズ調整
            size === "xs" && "w-2 h-2",
            size === "sm" && "w-2.5 h-2.5",
            size === "default" && "w-3 h-3",
            size === "lg" && "w-3.5 h-3.5",
            size === "xl" && "w-4 h-4"
          )}
          aria-hidden="true"
        />
      )}
      {showLabel && (
        <span className="font-medium">
          {config.label}
        </span>
      )}
    </Badge>
  );
}

// 優先度の表示順序を取得するヘルパー関数
export function getPriorityOrder(priority?: TaskPriority): number {
  if (!priority) return 999; // 優先度未設定は最後
  return priority; // 数値なのでそのまま返す
}

// 優先度の重要度を判定するヘルパー関数
export function isPriorityHigh(priority?: TaskPriority): boolean {
  return priority === 1;
}

export function isPriorityMedium(priority?: TaskPriority): boolean {
  return priority === 2;
}

export function isPriorityLow(priority?: TaskPriority): boolean {
  return priority === 3;
}