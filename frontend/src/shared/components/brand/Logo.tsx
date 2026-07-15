import { cn } from "@/shared/lib/utils";

type LogoSize = "sm" | "md" | "lg";
type LogoVariant = "symbol" | "horizontal" | "vertical";

const SYMBOL_SIZE: Record<LogoSize, string> = {
  sm: "size-5",
  md: "size-7",
  lg: "size-10",
};

const WORDMARK_SIZE: Record<LogoSize, string> = {
  sm: "text-sm",
  md: "text-lg",
  lg: "text-2xl",
};

/** Ring Gate mark ink — the identity spec's own #14130F/#FAF8F3, not `--foreground`: this is a locked brand asset, independent of the app's neutral UI palette. */
const INK = "text-[#14130F] dark:text-[#FAF8F3]";

function RingGateSymbol({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 100 100" fill="none" aria-hidden="true" className={className}>
      <circle cx="50" cy="50" r="36" stroke="currentColor" strokeWidth="10" />
      <rect x="40" y="4" width="20" height="34" fill="currentColor" />
      <rect x="40" y="62" width="20" height="34" fill="currentColor" />
    </svg>
  );
}

interface LogoProps {
  variant?: LogoVariant;
  size?: LogoSize;
  className?: string;
}

/** FlowDesk "Ring Gate" mark — geometry locked per the identity spec (100u grid, R 36u, stroke 10u, bars 20u×34u). */
export function Logo({ variant = "horizontal", size = "md", className }: LogoProps) {
  if (variant === "symbol") {
    return (
      <span role="img" aria-label="FlowDesk" className={cn("inline-flex", INK, className)}>
        <RingGateSymbol className={SYMBOL_SIZE[size]} />
      </span>
    );
  }

  return (
    <div
      className={cn(
        "inline-flex items-center",
        variant === "vertical" ? "flex-col gap-1.5" : "flex-row gap-2",
        INK,
        className,
      )}
    >
      <RingGateSymbol className={SYMBOL_SIZE[size]} />
      <span className={cn("font-semibold tracking-tight", WORDMARK_SIZE[size])}>FlowDesk</span>
    </div>
  );
}
