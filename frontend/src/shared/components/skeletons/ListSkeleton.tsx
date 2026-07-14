import { Skeleton } from "@/shared/components/ui/skeleton";

/** Generaliza o padrão hoje duplicado em `IssuesListSkeleton`/`ProjectsListSkeleton`. */
export function ListSkeleton({ rows = 8 }: { rows?: number }) {
  return (
    <div className="flex flex-col gap-2">
      {Array.from({ length: rows }).map((_, index) => (
        <Skeleton key={index} className="h-11 w-full" />
      ))}
    </div>
  );
}
