"use client";

import { cn } from "@/components/lib/utils";
import { Loader2 } from "lucide-react";

interface LoadingSpinnerProps {
  size?: "xs" | "sm" | "md" | "lg" | "xl";
  className?: string;
  text?: string;
  variant?: "default" | "dots" | "pulse" | "minimal";
  color?: "primary" | "secondary" | "muted";
}

/**
 * Enhanced loading spinner component with modern styling and multiple variants
 */
export function LoadingSpinner({
  size = "md",
  className,
  text,
  variant = "default",
  color = "primary"
}: LoadingSpinnerProps) {
  const sizeClasses = {
    xs: "h-3 w-3",
    sm: "h-4 w-4",
    md: "h-6 w-6",
    lg: "h-8 w-8",
    xl: "h-12 w-12"
  };

  const textSizeClasses = {
    xs: "text-xs",
    sm: "text-xs",
    md: "text-sm",
    lg: "text-base",
    xl: "text-lg"
  };

  const colorClasses = {
    primary: "text-primary",
    secondary: "text-secondary-foreground",
    muted: "text-muted-foreground"
  };

  if (variant === "dots") {
    return (
      <div className={cn("flex items-center justify-center gap-2 animate-fade-in-up", className)}>
        <div className="flex space-x-1 animate-loading-dots">
          <div className={cn(
            "rounded-full dot",
            sizeClasses[size],
            colorClasses[color],
            "bg-current"
          )} />
          <div className={cn(
            "rounded-full dot",
            sizeClasses[size],
            colorClasses[color],
            "bg-current"
          )} />
          <div className={cn(
            "rounded-full dot",
            sizeClasses[size],
            colorClasses[color],
            "bg-current"
          )} />
        </div>
        {text && (
          <span className={cn(
            textSizeClasses[size],
            "text-muted-foreground font-medium animate-subtle-pulse"
          )}>
            {text}
          </span>
        )}
      </div>
    );
  }

  if (variant === "pulse") {
    return (
      <div className={cn("flex items-center justify-center gap-3 animate-fade-in-up", className)}>
        <div className={cn(
          "rounded-full animate-subtle-pulse",
          sizeClasses[size],
          colorClasses[color],
          "bg-current"
        )} />
        {text && (
          <span className={cn(
            textSizeClasses[size],
            "text-muted-foreground font-medium animate-subtle-pulse"
          )}>
            {text}
          </span>
        )}
      </div>
    );
  }

  if (variant === "minimal") {
    return (
      <div className={cn("flex items-center justify-center gap-2 animate-fade-in-up", className)}>
        <div className={cn(
          "border-2 border-current border-t-transparent rounded-full animate-spin transition-all duration-300 ease-out",
          sizeClasses[size],
          colorClasses[color]
        )} />
        {text && (
          <span className={cn(
            textSizeClasses[size],
            "text-muted-foreground transition-all duration-300"
          )}>
            {text}
          </span>
        )}
      </div>
    );
  }

  // Default variant
  return (
    <div className={cn("flex items-center justify-center gap-3 animate-fade-in-up", className)}>
      <Loader2 className={cn(
        "animate-spin transition-all duration-300 ease-out",
        sizeClasses[size],
        colorClasses[color]
      )} />
      {text && (
        <span className={cn(
          textSizeClasses[size],
          "text-muted-foreground font-medium transition-all duration-300"
        )}>
          {text}
        </span>
      )}
    </div>
  );
}
