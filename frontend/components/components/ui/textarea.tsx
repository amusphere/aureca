import * as React from "react"

import { cn } from "@/components/lib/utils"

function Textarea({ className, ...props }: React.ComponentProps<"textarea">) {
  return (
    <textarea
      data-slot="textarea"
      className={cn(
        // Base styling with enhanced borders and backgrounds
        "flex min-h-20 w-full rounded-lg border-2 bg-background px-4 py-3 text-base transition-all duration-200 outline-none resize-y",
        // Enhanced border styling with subtle default state and hover effects
        "border-border/60 hover:border-border/80 hover:shadow-sm",
        // Improved placeholder styling with better contrast and subtle animation
        "placeholder:text-muted-foreground/70 placeholder:font-normal placeholder:tracking-normal placeholder:transition-colors placeholder:duration-200",
        // Enhanced focus states with smooth transitions and improved ring
        "focus:border-ring focus:ring-4 focus:ring-ring/15 focus:shadow-md focus:scale-[1.005] transform-gpu",
        // Better validation states with clear visual indicators and animations
        "aria-invalid:border-destructive aria-invalid:ring-4 aria-invalid:ring-destructive/15 aria-invalid:shadow-destructive/10",
        "data-[valid=true]:border-success data-[valid=true]:ring-4 data-[valid=true]:ring-success/15 data-[valid=true]:shadow-success/10",
        // Enhanced success state with subtle green glow
        "has-[:valid]:border-success/60 has-[:valid]:ring-2 has-[:valid]:ring-success/10",
        // Enhanced selection styling
        "selection:bg-primary selection:text-primary-foreground",
        // Dark mode enhancements with better contrast
        "dark:bg-background/50 dark:border-border/40 dark:hover:border-border/60 dark:hover:shadow-md",
        "dark:focus:border-ring dark:focus:ring-ring/20 dark:focus:shadow-ring/5",
        // Improved disabled state with better visual feedback
        "disabled:cursor-not-allowed disabled:opacity-60 disabled:bg-muted/30 disabled:border-border/30 disabled:resize-none disabled:shadow-none disabled:transform-none",
        // Text sizing responsive with better mobile experience
        "text-base md:text-sm",
        // Enhanced resize handle styling
        "resize-y [&::-webkit-resizer]:bg-muted-foreground/20 [&::-webkit-resizer]:rounded-br-lg",
        className
      )}
      {...props}
    />
  )
}

export { Textarea }
