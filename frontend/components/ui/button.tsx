import { ButtonHTMLAttributes, forwardRef } from "react";

type Variant = "primary" | "ghost";

export const Button = forwardRef<HTMLButtonElement, ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant }>(
  ({ variant = "primary", className = "", ...props }, ref) => {
    const base = "inline-flex items-center justify-center rounded-md px-4 py-2 text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed";
    const styles: Record<Variant, string> = {
      primary: "bg-accent text-white hover:bg-accent-soft",
      ghost: "bg-transparent text-ink dark:text-paper border border-ink/15 dark:border-paper/20 hover:bg-ink/5 dark:hover:bg-paper/5",
    };
    return <button ref={ref} className={`${base} ${styles[variant]} ${className}`} {...props} />;
  }
);
Button.displayName = "Button";
