import { formatLongDate, getGreeting } from "@/shared/lib/date";

import { useMyRadarIssues } from "../hooks";
import { ActiveProjectsWidget } from "./ActiveProjectsWidget";
import { MyIssuesWidget } from "./MyIssuesWidget";
import { QuickActions } from "./QuickActions";
import { RecentActivityWidget } from "./RecentActivityWidget";

export function DashboardView({
  workspaceId,
  workspaceSlug,
  userName,
  userId,
}: {
  workspaceId: string;
  workspaceSlug: string;
  userName: string;
  userId: string;
}) {
  const firstName = userName.split(" ")[0];
  const radar = useMyRadarIssues(workspaceId, userId);
  const resumo = radar.isLoading
    ? undefined
    : `${radar.inProgressCount} em andamento e ${radar.queuedCount} na fila no seu radar.`;

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-1.5">
        <h1 className="font-heading text-3xl font-semibold tracking-tight">
          {getGreeting()}, {firstName}.
        </h1>
        <p className="text-[13.5px] text-t2">
          {formatLongDate()}
          {resumo && ` — ${resumo}`}
        </p>
      </div>

      <QuickActions workspaceId={workspaceId} />

      <div className="grid items-start gap-4 lg:grid-cols-[3fr_2fr]">
        <div className="flex flex-col gap-4">
          <MyIssuesWidget workspaceId={workspaceId} workspaceSlug={workspaceSlug} userId={userId} />
          <ActiveProjectsWidget workspaceId={workspaceId} workspaceSlug={workspaceSlug} />
        </div>
        <RecentActivityWidget workspaceId={workspaceId} workspaceSlug={workspaceSlug} />
      </div>
    </div>
  );
}
