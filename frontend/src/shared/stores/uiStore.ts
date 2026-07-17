import { create } from "zustand";

/**
 * Estado de UI cliente-only (nunca espelha dado de servidor — CLAUDE.md §12/
 * docs/05-frontend.md §4). Hoje só o colapso da Sidebar; qualquer novo estado
 * efêmero de UI (ex.: filtros em edição antes de aplicar) entra aqui, não em
 * um store novo por feature, até que o volume justifique separar.
 */
interface UiState {
  isSidebarCollapsed: boolean;
  toggleSidebar: () => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
  isMobileNavOpen: boolean;
  setMobileNavOpen: (open: boolean) => void;
  isCommandPaletteOpen: boolean;
  setCommandPaletteOpen: (open: boolean) => void;
}

export const useUiStore = create<UiState>((set) => ({
  isSidebarCollapsed: false,
  toggleSidebar: () => set((state) => ({ isSidebarCollapsed: !state.isSidebarCollapsed })),
  setSidebarCollapsed: (collapsed) => set({ isSidebarCollapsed: collapsed }),
  isMobileNavOpen: false,
  setMobileNavOpen: (open) => set({ isMobileNavOpen: open }),
  isCommandPaletteOpen: false,
  setCommandPaletteOpen: (open) => set({ isCommandPaletteOpen: open }),
}));
