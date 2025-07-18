import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/components/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-lg text-sm font-medium transition-all duration-300 ease-out disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg:not([class*='size-'])]:size-4 shrink-0 [&_svg]:shrink-0 outline-none focus-visible:ring-4 focus-visible:ring-ring/30 focus-visible:ring-offset-2 focus-visible:ring-offset-background focus-visible:border-ring focus-visible:shadow-lg active:scale-[0.97] transform-gpu relative overflow-hidden before:absolute before:inset-0 before:bg-gradient-to-r before:opacity-0 before:transition-all before:duration-300 hover:before:opacity-15 after:absolute after:inset-0 after:bg-gradient-to-t after:from-white/10 after:to-transparent after:opacity-0 after:transition-all after:duration-300 hover:after:opacity-100 backdrop-blur-sm",
  {
    variants: {
      variant: {
        default:
          "bg-primary text-primary-foreground shadow-lg shadow-primary/30 hover:bg-primary-hover hover:shadow-xl hover:shadow-primary/40 hover:scale-[1.02] active:shadow-md active:shadow-primary/25 border border-primary/20 hover:border-primary/30 before:from-white before:to-transparent backdrop-blur-sm ring-offset-background transition-all duration-300 ease-out",
        destructive:
          "bg-destructive text-destructive-foreground shadow-lg shadow-destructive/30 hover:bg-destructive/90 hover:shadow-xl hover:shadow-destructive/40 hover:scale-[1.02] focus-visible:ring-destructive/25 active:shadow-md active:shadow-destructive/25 border border-destructive/25 hover:border-destructive/35 before:from-white before:to-transparent backdrop-blur-sm transition-all duration-300 ease-out",
        outline:
          "border-2 border-border/60 bg-background/80 backdrop-blur-sm shadow-sm hover:bg-accent hover:text-accent-foreground hover:border-border/80 hover:shadow-lg hover:scale-[1.02] dark:border-border/40 dark:hover:border-border/60 active:shadow-sm hover:bg-accent/80 before:from-accent before:to-transparent transition-all duration-300 ease-out",
        secondary:
          "bg-secondary text-secondary-foreground shadow-md shadow-secondary/15 hover:bg-secondary/80 hover:shadow-lg hover:shadow-secondary/25 hover:scale-[1.02] active:shadow-sm border border-secondary/20 hover:border-secondary/30 before:from-white before:to-transparent dark:before:from-white/15 backdrop-blur-sm transition-all duration-300 ease-out",
        ghost:
          "hover:bg-accent/80 hover:text-accent-foreground hover:scale-[1.02] hover:shadow-sm dark:hover:bg-accent/50 backdrop-blur-sm before:from-accent before:to-transparent transition-all duration-300 ease-out",
        link: "text-primary underline-offset-4 hover:underline hover:text-primary-hover transition-all duration-300 ease-out hover:scale-[1.01] before:hidden after:hidden",
        success:
          "bg-success text-success-foreground shadow-lg shadow-success/30 hover:bg-success/90 hover:shadow-xl hover:shadow-success/40 hover:scale-[1.02] focus-visible:ring-success/25 active:shadow-md active:shadow-success/25 border border-success/25 hover:border-success/35 before:from-white before:to-transparent backdrop-blur-sm transition-all duration-300 ease-out",
        warning:
          "bg-warning text-warning-foreground shadow-lg shadow-warning/30 hover:bg-warning/90 hover:shadow-xl hover:shadow-warning/40 hover:scale-[1.02] focus-visible:ring-warning/25 active:shadow-md active:shadow-warning/25 border border-warning/25 hover:border-warning/35 before:from-white before:to-transparent backdrop-blur-sm transition-all duration-300 ease-out",
        info:
          "bg-info text-info-foreground shadow-lg shadow-info/30 hover:bg-info/90 hover:shadow-xl hover:shadow-info/40 hover:scale-[1.02] focus-visible:ring-info/25 active:shadow-md active:shadow-info/25 border border-info/25 hover:border-info/35 before:from-white before:to-transparent backdrop-blur-sm transition-all duration-300 ease-out",
        // Enhanced accent variants using the new color system
        "accent-blue":
          "bg-accent-blue text-white shadow-lg shadow-accent-blue/30 hover:bg-accent-blue/90 hover:shadow-xl hover:shadow-accent-blue/40 hover:scale-[1.02] focus-visible:ring-accent-blue/25 active:shadow-md active:shadow-accent-blue/25 border border-accent-blue/25 hover:border-accent-blue/35 before:from-white before:to-transparent backdrop-blur-sm transition-all duration-300 ease-out",
        "accent-green":
          "bg-accent-green text-white shadow-lg shadow-accent-green/30 hover:bg-accent-green/90 hover:shadow-xl hover:shadow-accent-green/40 hover:scale-[1.02] focus-visible:ring-accent-green/25 active:shadow-md active:shadow-accent-green/25 border border-accent-green/25 hover:border-accent-green/35 before:from-white before:to-transparent backdrop-blur-sm transition-all duration-300 ease-out",
        "accent-orange":
          "bg-accent-orange text-white shadow-lg shadow-accent-orange/30 hover:bg-accent-orange/90 hover:shadow-xl hover:shadow-accent-orange/40 hover:scale-[1.02] focus-visible:ring-accent-orange/25 active:shadow-md active:shadow-accent-orange/25 border border-accent-orange/25 hover:border-accent-orange/35 before:from-white before:to-transparent backdrop-blur-sm transition-all duration-300 ease-out",
        "accent-purple":
          "bg-accent-purple text-white shadow-lg shadow-accent-purple/30 hover:bg-accent-purple/90 hover:shadow-xl hover:shadow-accent-purple/40 hover:scale-[1.02] focus-visible:ring-accent-purple/25 active:shadow-md active:shadow-accent-purple/25 border border-accent-purple/25 hover:border-accent-purple/35 before:from-white before:to-transparent backdrop-blur-sm transition-all duration-300 ease-out",
      },
      size: {
        default: "h-10 px-5 py-2.5 has-[>svg]:px-4 text-sm font-medium",
        sm: "h-8 rounded-md gap-1.5 px-3 py-1.5 text-xs font-medium has-[>svg]:px-2.5",
        lg: "h-12 rounded-lg px-8 py-3 text-base font-semibold has-[>svg]:px-6",
        xl: "h-14 rounded-xl px-10 py-4 text-lg font-semibold has-[>svg]:px-8",
        icon: "size-10 p-0 rounded-lg [&_svg]:size-4 flex-shrink-0 min-w-10 min-h-10 justify-center items-center shadow-sm hover:shadow-md",
        "icon-sm": "size-8 p-0 rounded-md [&_svg]:size-3.5 flex-shrink-0 min-w-8 min-h-8 justify-center items-center shadow-sm hover:shadow-md",
        "icon-lg": "size-12 p-0 rounded-lg [&_svg]:size-5 flex-shrink-0 min-w-12 min-h-12 justify-center items-center shadow-md hover:shadow-lg",
        "icon-xl": "size-14 p-0 rounded-xl [&_svg]:size-6 flex-shrink-0 min-w-14 min-h-14 justify-center items-center shadow-md hover:shadow-lg",
        "icon-xs": "size-6 p-0 rounded [&_svg]:size-3 flex-shrink-0 min-w-6 min-h-6 justify-center items-center shadow-sm hover:shadow-md",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

function Button({
  className,
  variant,
  size,
  asChild = false,
  ...props
}: React.ComponentProps<"button"> &
  VariantProps<typeof buttonVariants> & {
    asChild?: boolean
  }) {
  const Comp = asChild ? Slot : "button"

  return (
    <Comp
      data-slot="button"
      className={cn(buttonVariants({ variant, size, className }))}
      {...props}
    />
  )
}

export { Button, buttonVariants }
