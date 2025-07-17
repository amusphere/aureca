import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"
import * as React from "react"

import { cn } from "@/components/lib/utils"

const badgeVariants = cva(
  "inline-flex items-center justify-center rounded-lg border px-2.5 py-1 text-xs font-semibold w-fit whitespace-nowrap shrink-0 [&>svg]:size-3 gap-1.5 [&>svg]:pointer-events-none focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px] aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40 aria-invalid:border-destructive transition-all duration-300 ease-out overflow-hidden shadow-sm relative before:absolute before:inset-0 before:bg-gradient-to-r before:opacity-0 before:transition-all before:duration-300 [a&]:hover:before:opacity-20 transform-gpu backdrop-blur-sm",
  {
    variants: {
      variant: {
        default:
          "border-transparent bg-primary text-primary-foreground shadow-primary/25 [a&]:hover:bg-primary-hover [a&]:hover:shadow-lg [a&]:hover:shadow-primary/35 [a&]:hover:scale-[1.05] [a&]:active:scale-[0.98] before:from-white before:to-transparent transition-all duration-300 ease-out",
        secondary:
          "border-transparent bg-secondary text-secondary-foreground shadow-secondary/15 [a&]:hover:bg-secondary/80 [a&]:hover:shadow-lg [a&]:hover:shadow-secondary/25 [a&]:hover:scale-[1.05] [a&]:active:scale-[0.98] before:from-white before:to-transparent dark:before:from-white/15 transition-all duration-300 ease-out",
        destructive:
          "border-transparent bg-destructive text-destructive-foreground shadow-destructive/30 [a&]:hover:bg-destructive/90 [a&]:hover:shadow-lg [a&]:hover:shadow-destructive/40 [a&]:hover:scale-[1.05] [a&]:active:scale-[0.98] focus-visible:ring-destructive/25 before:from-white before:to-transparent transition-all duration-300 ease-out",
        success:
          "border-transparent bg-success text-success-foreground shadow-success/30 [a&]:hover:bg-success/90 [a&]:hover:shadow-lg [a&]:hover:shadow-success/40 [a&]:hover:scale-[1.05] [a&]:active:scale-[0.98] focus-visible:ring-success/25 before:from-white before:to-transparent transition-all duration-300 ease-out",
        warning:
          "border-transparent bg-warning text-warning-foreground shadow-warning/30 [a&]:hover:bg-warning/90 [a&]:hover:shadow-lg [a&]:hover:shadow-warning/40 [a&]:hover:scale-[1.05] [a&]:active:scale-[0.98] focus-visible:ring-warning/25 before:from-white before:to-transparent transition-all duration-300 ease-out",
        info:
          "border-transparent bg-info text-info-foreground shadow-info/30 [a&]:hover:bg-info/90 [a&]:hover:shadow-lg [a&]:hover:shadow-info/40 [a&]:hover:scale-[1.05] [a&]:active:scale-[0.98] focus-visible:ring-info/25 before:from-white before:to-transparent transition-all duration-300 ease-out",
        outline:
          "text-foreground border-border/60 bg-background/60 backdrop-blur-sm [a&]:hover:bg-accent [a&]:hover:text-accent-foreground [a&]:hover:border-border/80 [a&]:hover:shadow-lg [a&]:hover:scale-[1.05] [a&]:active:scale-[0.98] before:from-accent before:to-transparent transition-all duration-300 ease-out",
        ghost:
          "border-transparent bg-transparent text-foreground [a&]:hover:bg-accent/80 [a&]:hover:text-accent-foreground [a&]:hover:shadow-sm [a&]:hover:scale-[1.05] [a&]:active:scale-[0.98] before:from-accent before:to-transparent transition-all duration-300 ease-out",
        // Enhanced accent variants using the new color system
        "accent-blue":
          "border-transparent bg-accent-blue/20 text-accent-blue border-accent-blue/30 shadow-accent-blue/20 [a&]:hover:bg-accent-blue/30 [a&]:hover:shadow-lg [a&]:hover:shadow-accent-blue/30 [a&]:hover:scale-[1.05] [a&]:active:scale-[0.98] before:from-accent-blue/20 before:to-transparent transition-all duration-300 ease-out",
        "accent-green":
          "border-transparent bg-accent-green/20 text-accent-green border-accent-green/30 shadow-accent-green/20 [a&]:hover:bg-accent-green/30 [a&]:hover:shadow-lg [a&]:hover:shadow-accent-green/30 [a&]:hover:scale-[1.05] [a&]:active:scale-[0.98] before:from-accent-green/20 before:to-transparent transition-all duration-300 ease-out",
        "accent-orange":
          "border-transparent bg-accent-orange/20 text-accent-orange border-accent-orange/30 shadow-accent-orange/20 [a&]:hover:bg-accent-orange/30 [a&]:hover:shadow-lg [a&]:hover:shadow-accent-orange/30 [a&]:hover:scale-[1.05] [a&]:active:scale-[0.98] before:from-accent-orange/20 before:to-transparent transition-all duration-300 ease-out",
        "accent-purple":
          "border-transparent bg-accent-purple/20 text-accent-purple border-accent-purple/30 shadow-accent-purple/20 [a&]:hover:bg-accent-purple/30 [a&]:hover:shadow-lg [a&]:hover:shadow-accent-purple/30 [a&]:hover:scale-[1.05] [a&]:active:scale-[0.98] before:from-accent-purple/20 before:to-transparent transition-all duration-300 ease-out",
        // Enhanced status-specific variants with better visual hierarchy and smooth transitions
        "status-pending":
          "border-transparent bg-accent-orange/15 text-accent-orange border-accent-orange/25 shadow-accent-orange/15 [a&]:hover:bg-accent-orange/25 [a&]:hover:shadow-lg [a&]:hover:shadow-accent-orange/25 [a&]:hover:scale-[1.05] [a&]:active:scale-[0.98] before:from-accent-orange/15 before:to-transparent transition-all duration-300 ease-out",
        "status-in-progress":
          "border-transparent bg-accent-blue/15 text-accent-blue border-accent-blue/25 shadow-accent-blue/15 [a&]:hover:bg-accent-blue/25 [a&]:hover:shadow-lg [a&]:hover:shadow-accent-blue/25 [a&]:hover:scale-[1.05] [a&]:active:scale-[0.98] before:from-accent-blue/15 before:to-transparent transition-all duration-300 ease-out",
        "status-completed":
          "border-transparent bg-success/15 text-success border-success/25 shadow-success/15 [a&]:hover:bg-success/25 [a&]:hover:shadow-lg [a&]:hover:shadow-success/25 [a&]:hover:scale-[1.05] [a&]:active:scale-[0.98] before:from-success/15 before:to-transparent transition-all duration-300 ease-out",
        "status-cancelled":
          "border-transparent bg-muted/50 text-muted-foreground border-muted/70 shadow-muted/10 [a&]:hover:bg-muted/70 [a&]:hover:shadow-lg [a&]:hover:shadow-muted/20 [a&]:hover:scale-[1.05] [a&]:active:scale-[0.98] before:from-muted/15 before:to-transparent transition-all duration-300 ease-out",
        "priority-high":
          "border-transparent bg-destructive/15 text-destructive border-destructive/25 shadow-destructive/15 [a&]:hover:bg-destructive/25 [a&]:hover:shadow-lg [a&]:hover:shadow-destructive/25 [a&]:hover:scale-[1.05] [a&]:active:scale-[0.98] before:from-destructive/15 before:to-transparent transition-all duration-300 ease-out",
        "priority-medium":
          "border-transparent bg-warning/15 text-warning border-warning/25 shadow-warning/15 [a&]:hover:bg-warning/25 [a&]:hover:shadow-lg [a&]:hover:shadow-warning/25 [a&]:hover:scale-[1.05] [a&]:active:scale-[0.98] before:from-warning/15 before:to-transparent transition-all duration-300 ease-out",
        "priority-low":
          "border-transparent bg-info/15 text-info border-info/25 shadow-info/15 [a&]:hover:bg-info/25 [a&]:hover:shadow-lg [a&]:hover:shadow-info/25 [a&]:hover:scale-[1.05] [a&]:active:scale-[0.98] before:from-info/15 before:to-transparent transition-all duration-300 ease-out",
      },
      size: {
        xs: "px-1.5 py-0.5 text-xs rounded-md [&>svg]:size-2.5 gap-1",
        sm: "px-2 py-0.5 text-xs rounded-md [&>svg]:size-2.5 gap-1",
        default: "px-2.5 py-1 text-xs [&>svg]:size-3 gap-1.5",
        lg: "px-3 py-1.5 text-sm rounded-lg [&>svg]:size-3.5 gap-1.5",
        xl: "px-4 py-2 text-sm rounded-xl [&>svg]:size-4 gap-2",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

function Badge({
  className,
  variant,
  size,
  asChild = false,
  ...props
}: React.ComponentProps<"span"> &
  VariantProps<typeof badgeVariants> & { asChild?: boolean }) {
  const Comp = asChild ? Slot : "span"

  return (
    <Comp
      data-slot="badge"
      className={cn(badgeVariants({ variant, size }), className)}
      {...props}
    />
  )
}

export { Badge, badgeVariants }
export type BadgeVariant = VariantProps<typeof badgeVariants>['variant']
