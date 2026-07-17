import { CreateIssueDialog } from "@/features/issues/components/CreateIssueDialog";
import { CreateProjectDialog } from "@/features/projects/components/CreateProjectDialog";

export function QuickActions({ workspaceId }: { workspaceId: string }) {
  return (
    <div className="flex flex-wrap gap-2">
      <CreateIssueDialog workspaceId={workspaceId} />
      <CreateProjectDialog workspaceId={workspaceId} />
    </div>
  );
}
