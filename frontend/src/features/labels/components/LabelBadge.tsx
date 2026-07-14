import { Badge } from "@/shared/components/ui/badge";

import type { Label } from "../types";

export function LabelBadge({ label }: { label: Label }) {
  return (
    <Badge variant="outline" className="gap-1.5">
      <span
        className="inline-block size-2 shrink-0 rounded-full"
        style={{ backgroundColor: label.color }}
      />
      {label.name}
    </Badge>
  );
}
