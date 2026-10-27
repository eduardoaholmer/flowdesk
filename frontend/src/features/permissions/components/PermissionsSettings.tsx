import { Fragment } from "react";

import { ErrorState } from "@/shared/components/feedback/ErrorState";
import { ListSkeleton } from "@/shared/components/skeletons/ListSkeleton";
import { Badge } from "@/shared/components/ui/badge";
import { Switch } from "@/shared/components/ui/switch";

import {
  OVERRIDABLE_ROLE_LABELS,
  OVERRIDABLE_ROLE_ORDER,
  PERMISSION_DOMAIN_LABELS,
  PERMISSION_DOMAIN_ORDER,
  PERMISSION_LABELS,
  permissionDomain,
} from "../constants";
import { usePermissionMatrix, useSetPermissionOverride } from "../hooks";
import type { OverridableRole, PermissionMatrixEntry } from "../types";

export function PermissionsSettings({ workspaceId }: { workspaceId: string }) {
  const { data, isLoading, isError, refetch } = usePermissionMatrix(workspaceId);
  const setOverride = useSetPermissionOverride(workspaceId);

  if (isLoading) {
    return <ListSkeleton rows={8} />;
  }
  if (isError || !data) {
    return (
      <ErrorState message="Não foi possível carregar as permissões." onRetry={() => refetch()} />
    );
  }

  const byRoleAndPermission = new Map(
    data.map((entry) => [`${entry.role}:${entry.permission}`, entry]),
  );
  const permissionsByDomain = new Map<string, string[]>();
  for (const permission of new Set(data.map((entry) => entry.permission))) {
    const domain = permissionDomain(permission);
    const list = permissionsByDomain.get(domain) ?? [];
    list.push(permission);
    permissionsByDomain.set(domain, list);
  }

  function entryFor(role: OverridableRole, permission: string): PermissionMatrixEntry | undefined {
    return byRoleAndPermission.get(`${role}:${permission}`);
  }

  return (
    <div className="flex flex-col gap-4">
      <p className="text-sm text-t2">
        Ligue ou desligue permissões individuais para Admin, Membro e Convidado neste workspace —
        desligar uma permissão remove a ação por completo para aquele papel.
      </p>

      <div className="overflow-x-auto rounded-xl border">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b bg-muted/40">
              <th className="px-4 py-2 text-left font-medium">Permissão</th>
              {OVERRIDABLE_ROLE_ORDER.map((role) => (
                <th key={role} className="px-4 py-2 text-center font-medium">
                  {OVERRIDABLE_ROLE_LABELS[role]}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {PERMISSION_DOMAIN_ORDER.filter((domain) => permissionsByDomain.has(domain)).map(
              (domain) => (
                <Fragment key={domain}>
                  <tr className="border-b bg-muted/20">
                    <td colSpan={OVERRIDABLE_ROLE_ORDER.length + 1} className="px-4 py-1.5">
                      <span className="text-[10.5px] font-semibold tracking-wide text-t3 uppercase">
                        {PERMISSION_DOMAIN_LABELS[domain] ?? domain}
                      </span>
                    </td>
                  </tr>
                  {permissionsByDomain.get(domain)?.map((permission) => (
                    <tr key={permission} className="border-b last:border-b-0">
                      <td className="px-4 py-2">{PERMISSION_LABELS[permission] ?? permission}</td>
                      {OVERRIDABLE_ROLE_ORDER.map((role) => {
                        const entry = entryFor(role, permission);
                        if (!entry) return <td key={role} />;
                        return (
                          <td key={role} className="px-4 py-2">
                            <div className="flex items-center justify-center gap-1.5">
                              <Switch
                                checked={entry.effective}
                                disabled={setOverride.isPending}
                                aria-label={`${PERMISSION_LABELS[permission] ?? permission} — ${OVERRIDABLE_ROLE_LABELS[role]}`}
                                onCheckedChange={(checked) =>
                                  setOverride.mutate({ role, permission, granted: checked })
                                }
                              />
                              {entry.is_override && (
                                <Badge variant="secondary" className="text-[10px]">
                                  Customizado
                                </Badge>
                              )}
                            </div>
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </Fragment>
              ),
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
