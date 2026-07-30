import type { CSSProperties } from "react";

import type { WorkflowStateCategory } from "@/features/workflow-states/types";

/** Glifo de círculo por categoria de status, conforme o handoff de redesign do
 * Milestone 7 (`docs/design-handoff/2026-07-20-redesign-gestor/data.js`, objeto
 * `STATUS`). Categoria (não o nome customizável do status — Sprint 9.2/ADR-056)
 * é a chave, já que é o único valor fixo que sobra por status. */

const OUTER_BASE: CSSProperties = {
  width: 14,
  height: 14,
  borderRadius: "50%",
  display: "inline-flex",
  alignItems: "center",
  justifyContent: "center",
  flex: "none",
  boxSizing: "border-box",
};

const GLYPH_BASE: CSSProperties = {
  lineHeight: 1,
  fontWeight: 800,
};

type StatusGlyph = { outer: CSSProperties; inner: CSSProperties | null; glyph: string };

const GLYPHS: Record<WorkflowStateCategory, StatusGlyph> = {
  BACKLOG: { outer: { ...OUTER_BASE, border: "1.5px dashed var(--t3)" }, inner: null, glyph: "" },
  UNSTARTED: { outer: { ...OUTER_BASE, border: "1.5px solid var(--t2)" }, inner: null, glyph: "" },
  STARTED: {
    outer: { ...OUTER_BASE, border: "1.5px solid var(--amber)" },
    inner: {
      width: 7,
      height: 7,
      borderRadius: "50%",
      background: "conic-gradient(var(--amber) 0 180deg, transparent 180deg 360deg)",
      display: "block",
    },
    glyph: "",
  },
  COMPLETED: {
    outer: { ...OUTER_BASE, background: "var(--green)" },
    inner: { ...GLYPH_BASE, color: "var(--background)", fontSize: 9 },
    glyph: "✓",
  },
  CANCELED: {
    outer: { ...OUTER_BASE, background: "var(--t3)" },
    inner: { ...GLYPH_BASE, color: "var(--background)", fontSize: 10 },
    glyph: "×",
  },
};

export function IssueStatusIcon({ category }: { category: WorkflowStateCategory }) {
  const { outer, inner, glyph } = GLYPHS[category];
  return (
    <span style={outer} aria-hidden="true">
      {inner && <span style={inner}>{glyph}</span>}
    </span>
  );
}
