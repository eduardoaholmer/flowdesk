import type { CSSProperties } from "react";

import type { IssuePriority } from "../types";

/** Glifo de "barras de equalizador" por prioridade, conforme o handoff de
 * redesign do Milestone 7 (`docs/design-handoff/2026-07-20-redesign-gestor/data.js`,
 * objeto `PRIORITY`) — substitui os ícones lucide anteriores (ver
 * design-system/badges.md). `var(--text)` do handoff mapeia para `--foreground`
 * já existente, não duplicado como token novo. */

const BOX_BASE: CSSProperties = {
  width: 15,
  height: 14,
  display: "inline-flex",
  alignItems: "center",
  justifyContent: "center",
  flex: "none",
};

const GLYPH_BASE: CSSProperties = { lineHeight: 1, fontWeight: 800 };

function bars(a: string, b: string, c: string): CSSProperties {
  return {
    width: 13,
    height: 11,
    flex: "none",
    backgroundImage: `linear-gradient(${a},${a}),linear-gradient(${b},${b}),linear-gradient(${c},${c})`,
    backgroundSize: "3px 45%,3px 72%,3px 100%",
    backgroundPosition: "0 100%,5px 100%,10px 100%",
    backgroundRepeat: "no-repeat",
  };
}

type PriorityGlyph = { outer: CSSProperties; inner: CSSProperties | null; glyph: string };

const GLYPHS: Record<IssuePriority, PriorityGlyph> = {
  URGENT: {
    outer: { ...BOX_BASE, background: "var(--destructive)", borderRadius: 3.5 },
    inner: { ...GLYPH_BASE, color: "var(--brand-paper)", fontSize: 10.5 },
    glyph: "!",
  },
  HIGH: {
    outer: bars("var(--foreground)", "var(--foreground)", "var(--foreground)"),
    inner: null,
    glyph: "",
  },
  MEDIUM: {
    outer: bars("var(--foreground)", "var(--foreground)", "var(--border2)"),
    inner: null,
    glyph: "",
  },
  LOW: {
    outer: bars("var(--foreground)", "var(--border2)", "var(--border2)"),
    inner: null,
    glyph: "",
  },
  NO_PRIORITY: {
    outer: { ...BOX_BASE },
    inner: { ...GLYPH_BASE, color: "var(--t3)", fontSize: 11, fontWeight: 700 },
    glyph: "—",
  },
};

export function IssuePriorityIcon({ priority }: { priority: IssuePriority }) {
  const { outer, inner, glyph } = GLYPHS[priority];
  return (
    <span style={outer} aria-hidden="true">
      {inner && <span style={inner}>{glyph}</span>}
    </span>
  );
}
