import { useState } from "react";
import { useSearchParams } from "react-router-dom";

import { ErrorState } from "@/shared/components/feedback/ErrorState";
import { Pagination } from "@/shared/components/navigation/Pagination";
import { ListSkeleton } from "@/shared/components/skeletons/ListSkeleton";
import { useDebouncedValue } from "@/shared/hooks/useDebouncedValue";
import { cn } from "@/shared/lib/utils";

import { useIssues } from "../hooks";
import type { IssuePriority, IssueSort, IssueStatus } from "../types";
import { IssuesEmptyState } from "./IssuesEmptyState";
import { IssuesTable } from "./IssuesTable";
import { IssuesToolbar } from "./IssuesToolbar";

const PER_PAGE = 20;

export function IssuesListPage({
  workspaceId,
  workspaceSlug,
}: {
  workspaceId: string;
  workspaceSlug: string;
}) {
  const [searchParams, setSearchParams] = useSearchParams();
  const [searchInput, setSearchInput] = useState(searchParams.get("q") ?? "");
  const debouncedSearch = useDebouncedValue(searchInput);

  const page = Number(searchParams.get("page") ?? "1");
  const status = (searchParams.get("status") as IssueStatus | null) ?? "ALL";
  const priority = (searchParams.get("priority") as IssuePriority | null) ?? "ALL";
  const projectId = searchParams.get("project_id") ?? "ALL";
  const sort = (searchParams.get("sort") as IssueSort | null) ?? "-updated_at";

  const { data, isLoading, isError, refetch, isPlaceholderData } = useIssues(workspaceId, {
    page,
    per_page: PER_PAGE,
    q: debouncedSearch || undefined,
    status: status === "ALL" ? undefined : status,
    priority: priority === "ALL" ? undefined : priority,
    project_id: projectId === "ALL" ? undefined : projectId,
    sort,
  });

  function updateParams(next: {
    q?: string;
    status?: IssueStatus | "ALL";
    priority?: IssuePriority | "ALL";
    project_id?: string | "ALL";
    sort?: IssueSort;
    page?: number;
  }) {
    setSearchParams((prev) => {
      const params = new URLSearchParams(prev);
      if (next.q !== undefined) {
        if (next.q) params.set("q", next.q);
        else params.delete("q");
        params.delete("page");
      }
      if (next.status !== undefined) {
        if (next.status !== "ALL") params.set("status", next.status);
        else params.delete("status");
        params.delete("page");
      }
      if (next.priority !== undefined) {
        if (next.priority !== "ALL") params.set("priority", next.priority);
        else params.delete("priority");
        params.delete("page");
      }
      if (next.project_id !== undefined) {
        if (next.project_id !== "ALL") params.set("project_id", next.project_id);
        else params.delete("project_id");
        params.delete("page");
      }
      if (next.sort !== undefined) {
        params.set("sort", next.sort);
        params.delete("page");
      }
      if (next.page !== undefined) {
        if (next.page > 1) params.set("page", String(next.page));
        else params.delete("page");
      }
      return params;
    });
  }

  const hasFilters =
    Boolean(debouncedSearch) || status !== "ALL" || priority !== "ALL" || projectId !== "ALL";

  return (
    <div className="flex flex-col gap-4">
      <div>
        <h1 className="text-lg font-semibold">Issues</h1>
        <p className="text-sm text-muted-foreground">Issues deste workspace.</p>
      </div>

      <IssuesToolbar
        workspaceId={workspaceId}
        search={searchInput}
        onSearchChange={(value) => {
          setSearchInput(value);
          updateParams({ q: value });
        }}
        status={status}
        onStatusChange={(value) => updateParams({ status: value })}
        priority={priority}
        onPriorityChange={(value) => updateParams({ priority: value })}
        projectId={projectId}
        onProjectChange={(value) => updateParams({ project_id: value })}
        sort={sort}
        onSortChange={(value) => updateParams({ sort: value })}
      />

      {isLoading ? (
        <ListSkeleton rows={8} />
      ) : isError ? (
        <ErrorState message="Não foi possível carregar as issues." onRetry={() => refetch()} />
      ) : data && data.data.length > 0 ? (
        <div className={cn("flex flex-col gap-4", isPlaceholderData && "opacity-60")}>
          <IssuesTable workspaceId={workspaceId} workspaceSlug={workspaceSlug} issues={data.data} />
          <Pagination
            meta={data.meta}
            itemLabel="issue"
            onPageChange={(next) => updateParams({ page: next })}
          />
        </div>
      ) : (
        <IssuesEmptyState workspaceId={workspaceId} hasFilters={hasFilters} />
      )}
    </div>
  );
}
