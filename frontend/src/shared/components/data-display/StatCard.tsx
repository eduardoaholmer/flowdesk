import type { LucideIcon } from "lucide-react";
import { TrendingDown, TrendingUp } from "lucide-react";

import { Card, CardContent, CardHeader } from "@/shared/components/ui/card";
import { CardSkeleton } from "@/shared/components/skeletons/CardSkeleton";
import { cn } from "@/shared/lib/utils";

interface StatCardProps {
  label: string;
  value: string | number;
  icon?: LucideIcon;
  /** Percentual de variação (ex.: 12 = "+12%", -8 = "-8%") — omitido sem tendência. */
  trend?: number;
  isLoading?: boolean;
  className?: string;
}

/** Métrica única em card — pensado para o dashboard da Sprint 9 (`features/dashboard/`, hoje placeholder). */
export function StatCard({ label, value, icon: Icon, trend, isLoading, className }: StatCardProps) {
  if (isLoading) {
    return <CardSkeleton />;
  }

  const TrendIcon = trend !== undefined && trend < 0 ? TrendingDown : TrendingUp;

  return (
    <Card className={className}>
      <CardHeader className="flex-row items-center justify-between">
        <span className="text-sm text-muted-foreground">{label}</span>
        {Icon && <Icon className="size-4 text-muted-foreground" />}
      </CardHeader>
      <CardContent className="flex items-baseline gap-2">
        <span className="font-heading text-2xl font-semibold">{value}</span>
        {trend !== undefined && (
          <span
            className={cn(
              "flex items-center gap-0.5 text-xs font-medium",
              trend < 0 ? "text-destructive" : "text-muted-foreground",
            )}
          >
            <TrendIcon className="size-3" />
            {Math.abs(trend)}%
          </span>
        )}
      </CardContent>
    </Card>
  );
}
