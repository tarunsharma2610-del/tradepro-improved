import { InputHTMLAttributes, forwardRef } from "react";

type Props = InputHTMLAttributes<HTMLInputElement> & { label: string; error?: string };

export const Input = forwardRef<HTMLInputElement, Props>(({ label, error, id, className = "", ...props }, ref) => {
  const inputId = id || label.toLowerCase().replace(/\s+/g, "-");
  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={inputId} className="text-sm font-medium text-ink/80 dark:text-paper/80">
        {label}
      </label>
      <input
        ref={ref}
        id={inputId}
        className={`rounded-md border border-ink/15 dark:border-paper/20 bg-white dark:bg-ink-soft px-3 py-2 text-sm text-ink dark:text-paper placeholder:text-ink/40 dark:placeholder:text-paper/40 focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent ${className}`}
        {...props}
      />
      {error && <span className="text-sm text-loss">{error}</span>}
    </div>
  );
});
Input.displayName = "Input";
