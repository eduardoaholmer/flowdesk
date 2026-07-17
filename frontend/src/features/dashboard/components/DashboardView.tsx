import { ActiveProjectsWidget } from "./ActiveProjectsWidget";
import { MyIssuesWidget } from "./MyIssuesWidget";
import { QuickActions } from "./QuickActions";
import { RecentActivityWidget } from "./RecentActivityWidget";

export function DashboardView({
  workspaceId,
  workspaceSlug,
  workspaceName,
  userName,
  userId,
}: {
  workspaceId: string;
  workspaceSlug: string;
  workspaceName: string;
  userName: string;
  userId: string;
}) {
  const firstName = userName.split(" ")[0];

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-1">
        <h1 className="text-lg font-semibold">Olá, {firstName}</h1>
        <p className="text-sm text-muted-foreground">{workspaceName}</p>
      </div>

      <QuickActions workspaceId={workspaceId} />

      <div className="grid gap-4 lg:grid-cols-2">
        <MyIssuesWidget workspaceId={workspaceId} workspaceSlug={workspaceSlug} userId={userId} />
        <RecentActivityWidget workspaceId={workspaceId} workspaceSlug={workspaceSlug} />
        <ActiveProjectsWidget workspaceId={workspaceId} workspaceSlug={workspaceSlug} />
      </div>
    </div>
  );
}
