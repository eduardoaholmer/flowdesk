import { Outlet } from "react-router-dom";

import { CommandPalette } from "@/shared/components/command-palette/CommandPalette";
import { PageContainer } from "@/shared/components/layout/PageContainer";
import { Sidebar } from "@/shared/components/layout/Sidebar";
import { Topbar } from "@/shared/components/layout/Topbar";

/**
 * `PageContainer` (largura máxima `xl`, o padrão certo para listas/tabelas — a
 * maioria das rotas autenticadas) envolve `<Outlet/>` aqui, não em cada página —
 * único ponto de padding/largura responsivo para toda rota autenticada (Milestone 3,
 * ADR-019). Uma página que precise de leitura mais estreita (ex.: um formulário
 * solitário) usa `ContentContainer` por dentro, sem declarar seu próprio `max-w-*`.
 */
export function AppLayout() {
  return (
    <div className="flex h-screen flex-col">
      <Topbar />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        <main className="flex-1 overflow-y-auto">
          <PageContainer>
            <Outlet />
          </PageContainer>
        </main>
      </div>
      <CommandPalette />
    </div>
  );
}
