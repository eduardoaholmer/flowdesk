import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/shared/components/ui/tabs";

import type { WorkspaceRole } from "../types";
import { WorkspaceGeneralSettings } from "./WorkspaceGeneralSettings";
import { WorkspaceInvitationsSettings } from "./WorkspaceInvitationsSettings";
import { WorkspaceMembersSettings } from "./WorkspaceMembersSettings";

export function WorkspaceSettingsPage({
  workspaceId,
  role,
}: {
  workspaceId: string;
  role: WorkspaceRole;
}) {
  const canManage = role === "OWNER" || role === "ADMIN";

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-lg font-semibold">Configurações do workspace</h1>
        <p className="text-sm text-muted-foreground">Nome, membros e convites deste workspace.</p>
      </div>

      <Tabs defaultValue="general">
        <TabsList>
          <TabsTrigger value="general">Geral</TabsTrigger>
          <TabsTrigger value="members">Membros</TabsTrigger>
          {canManage && <TabsTrigger value="invitations">Convites</TabsTrigger>}
        </TabsList>
        <TabsContent value="general" className="pt-4">
          <WorkspaceGeneralSettings
            workspaceId={workspaceId}
            canEdit={canManage}
            canDelete={role === "OWNER"}
          />
        </TabsContent>
        <TabsContent value="members" className="pt-4">
          <WorkspaceMembersSettings
            workspaceId={workspaceId}
            canManage={canManage}
            isOwner={role === "OWNER"}
          />
        </TabsContent>
        {canManage && (
          <TabsContent value="invitations" className="pt-4">
            <WorkspaceInvitationsSettings workspaceId={workspaceId} />
          </TabsContent>
        )}
      </Tabs>
    </div>
  );
}
