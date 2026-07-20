import { Skeleton } from "@/shared/components/ui/skeleton";

/** Casca de carregamento do board por status (`IssuesBoardView`, Sprint 16.1/M5). */
export function KanbanSkeleton({
  columns = 4,
  cardsPerColumn = 3,
}: {
  columns?: number;
  cardsPerColumn?: number;
}) {
  return (
    <div className="flex gap-4 overflow-x-auto">
      {Array.from({ length: columns }).map((_, columnIndex) => (
        <div key={columnIndex} className="flex w-64 shrink-0 flex-col gap-2">
          <Skeleton className="h-5 w-24" />
          {Array.from({ length: cardsPerColumn }).map((_, cardIndex) => (
            <Skeleton key={cardIndex} className="h-20 w-full" />
          ))}
        </div>
      ))}
    </div>
  );
}
