import { create } from "zustand";

const SIDEBAR_COLLAPSED_KEY = "flowdesk:sidebar-collapsed";

function readStoredSidebarCollapsed(): boolean {
  try {
    return window.localStorage.getItem(SIDEBAR_COLLAPSED_KEY) === "1";
  } catch {
    return false;
  }
}

function writeStoredSidebarCollapsed(collapsed: boolean): void {
  try {
    window.localStorage.setItem(SIDEBAR_COLLAPSED_KEY, collapsed ? "1" : "0");
  } catch {
    // Storage indisponível (modo privado, quota excedida) — segue só em memória.
  }
}

/**
 * Estado de UI cliente-only (nunca espelha dado de servidor — CLAUDE.md §12/
 * docs/05-frontend.md §4). Qualquer novo estado efêmero de UI (ex.: filtros em
 * edição antes de aplicar) entra aqui, não em um store novo por feature, até
 * que o volume justifique separar.
 */
interface UiState {
  isSidebarCollapsed: boolean;
  toggleSidebar: () => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
  isMobileNavOpen: boolean;
  setMobileNavOpen: (open: boolean) => void;
  isCommandPaletteOpen: boolean;
  setCommandPaletteOpen: (open: boolean) => void;
  isCreateIssueOpen: boolean;
  setCreateIssueOpen: (open: boolean) => void;
}

export const useUiStore = create<UiState>((set) => ({
  isSidebarCollapsed: readStoredSidebarCollapsed(),
  toggleSidebar: () =>
    set((state) => {
      const next = !state.isSidebarCollapsed;
      writeStoredSidebarCollapsed(next);
      return { isSidebarCollapsed: next };
    }),
  setSidebarCollapsed: (collapsed) => {
    writeStoredSidebarCollapsed(collapsed);
    set({ isSidebarCollapsed: collapsed });
  },
  isMobileNavOpen: false,
  setMobileNavOpen: (open) => set({ isMobileNavOpen: open }),
  isCommandPaletteOpen: false,
  setCommandPaletteOpen: (open) => set({ isCommandPaletteOpen: open }),
  isCreateIssueOpen: false,
  setCreateIssueOpen: (open) => set({ isCreateIssueOpen: open }),
}));
