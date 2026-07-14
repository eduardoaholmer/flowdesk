import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/shared/components/ui/table";

import type { Label } from "../types";
import { LabelBadge } from "./LabelBadge";
import { LabelRowActions } from "./LabelRowActions";

export function LabelsTable({ workspaceId, labels }: { workspaceId: string; labels: Label[] }) {
  return (
    <div className="rounded-xl border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Label</TableHead>
            <TableHead>Descrição</TableHead>
            <TableHead className="w-24 text-right">Ações</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {labels.map((label) => (
            <TableRow key={label.id}>
              <TableCell>
                <LabelBadge label={label} />
              </TableCell>
              <TableCell className="max-w-md truncate text-muted-foreground">
                {label.description || "—"}
              </TableCell>
              <TableCell>
                <div className="flex justify-end">
                  <LabelRowActions workspaceId={workspaceId} label={label} />
                </div>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
