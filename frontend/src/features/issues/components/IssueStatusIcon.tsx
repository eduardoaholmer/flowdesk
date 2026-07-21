import type { CSSProperties } from "react";

import type { IssueStatus } from "../types";

/** Glifo de círculo por status, conforme o handoff de redesign do Milestone 7
 * (`docs/design-handoff/2026-07-20-redesign-gestor/data.js`, objeto `STATUS`).
 * `IN_REVIEW` não existe no handoff (que modela só 5 status) — extensão própria
 * desta sprint: mesmo anel/preenchimento de `IN_PROGRESS` (âmbar), fatia maior
 * (270°) para comunicar "mais perto de concluído" sem inventar uma cor nova
 * (ver design-system/badges.md). */

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

const GLYPHS: Record<IssueStatus, StatusGlyph> = {
  BACKLOG: { outer: { ...OUTER_BASE, border: "1.5px dashed var(--t3)" }, inner: null, glyph: "" },
  TODO: { outer: { ...OUTER_BASE, border: "1.5px solid var(--t2)" }, inner: null, glyph: "" },
  IN_PROGRESS: {
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
  IN_REVIEW: {
    outer: { ...OUTER_BASE, border: "1.5px solid var(--amber)" },
    inner: {
      width: 7,
      height: 7,
      borderRadius: "50%",
      background: "conic-gradient(var(--amber) 0 270deg, transparent 270deg 360deg)",
      display: "block",
    },
    glyph: "",
  },
  DONE: {
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

export function IssueStatusIcon({ status }: { status: IssueStatus }) {
  const { outer, inner, glyph } = GLYPHS[status];
  return (
    <span style={outer} aria-hidden="true">
      {inner && <span style={inner}>{glyph}</span>}
    </span>
  );
}
