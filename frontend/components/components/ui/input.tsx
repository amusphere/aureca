import * as React from "react"

import { cn } from "@/components/lib/utils"

export interface InputProps extends React.ComponentProps<"input"> {
  error?: boolean;
  success?: boolean;
}

function Input({ className, type, error, success, ...props }: InputProps) {
  return (
    <input
      type={type}
      data-slot="input"
      data-error={error}
      data-success={success}
      className={cn(
        // Base styling with enhanced borders and backgrounds
        "flex h-10 w-full min-w-0 rounded-lg border-2 bg-background px-4 py-2.5 text-base transition-all duration-200 outline-none",
        // Enhanced border styling with subtle default state
        "border-border/60 hover:border-border/80 hover:shadow-sm",
        // Improved placeholder styling with better contrast and subtle animation
        "placeholder:text-muted-foreground/70 placeholder:font-normal placeholder:tracking-normal placeholder:transition-colors placeholder:duration-200",
        "focus:placeholder:text-muted-foreground/50",
        // Enhanced focus states with smooth transitions and improved ring
        "focus:border-ring focus:ring-4 focus:ring-ring/20 focus:ring-offset-2 focus:ring-offset-background focus:shadow-md focus:scale-[1.01] transform-gpu",
        // Better validation states with clear visual indicators and animations
        "aria-invalid:border-destructive aria-invalid:ring-4 aria-invalid:ring-destructive/15 aria-invalid:shadow-destructive/10",
        "data-[error=true]:border-destructive data-[error=true]:ring-4 data-[error=true]:ring-destructive/15 data-[error=true]:shadow-destructive/10",
        "data-[error=true]:focus:border-destructive data-[error=true]:focus:ring-destructive/20",
        // Enhanced success state with subtle green glow
        "data-[success=true]:border-success data-[success=true]:ring-4 data-[success=true]:ring-success/15 data-[success=true]:shadow-success/10",
        "data-[success=true]:focus:border-success data-[success=true]:focus:ring-success/20",
        "has-[:valid]:border-success/60 has-[:valid]:ring-2 has-[:valid]:ring-success/10",
        // File input specific styling with better appearance
        "file:border-0 file:bg-transparent file:text-sm file:font-medium file:text-foreground file:mr-4 file:py-1 file:px-2 file:rounded file:bg-muted/50 file:hover:bg-muted file:transition-colors",
        // Enhanced selection styling
        "selection:bg-primary selection:text-primary-foreground",
        // Dark mode enhancements with better contrast
        "dark:bg-background/50 dark:border-border/40 dark:hover:border-border/60 dark:hover:shadow-md",
        "dark:focus:border-ring dark:focus:ring-ring/20 dark:focus:shadow-ring/5",
        "dark:data-[error=true]:shadow-destructive/5 dark:data-[success=true]:shadow-success/5",
        // Improved disabled state with better visual feedback
        "disabled:cursor-not-allowed disabled:opacity-60 disabled:bg-muted/30 disabled:border-border/30 disabled:shadow-none disabled:transform-none",
        "disabled:placeholder:text-muted-foreground/40",
        // Text sizing responsive with better mobile experience
        "text-base md:text-sm",
        // Enhanced autofill styling
        "autofill:bg-background autofill:text-foreground autofill:shadow-[inset_0_0_0px_1000px_hsl(var(--background))]",
        // Loading state styling
        "data-[loading=true]:animate-pulse data-[loading=true]:cursor-wait",
        className
      )}
      {...props}
    />
  )
}

export { Input }
