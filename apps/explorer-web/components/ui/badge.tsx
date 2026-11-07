import * as React from "react";
import { cn } from "@/lib/utils";

const VARIANTS = {
  default: "border-transparent bg-primary text-primary-foreground",
  secondary: "border-transparent bg-secondary text-secondary-foreground",
  outline: "text-foreground",
  destructive: "border-transparent bg-destructive text-destructive-foreground",
} as const;

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Visual style; callers use "secondary" for neutral counts and labels. */
  variant?: keyof typeof VARIANTS;
}

export function Badge({ className, variant = "secondary", ...props }: BadgeProps) {
  return (
    <div
      className={cn(
        "inline-flex items-center rounded-md border px-2.5 py-0.5 text-xs font-semibold transition-colors",
        VARIANTS[variant],
        className,
      )}
      {...props}
    />
  );
}
