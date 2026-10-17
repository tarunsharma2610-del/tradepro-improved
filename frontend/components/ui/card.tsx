import { HTMLAttributes } from "react";

export function Card({ className = "", ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={`rounded-lg border border-ink/10 dark:border-paper/10 bg-white dark:bg-ink-soft p-6 shadow-sm ${className}`}
      {...props}
    />
  );
}
