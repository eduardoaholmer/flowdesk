import "@testing-library/jest-dom/vitest";

import { cleanup } from "@testing-library/react";
import { afterEach, vi } from "vitest";

/**
 * `test.globals` não está ligado em `vite.config.ts` — o registro automático de
 * cleanup do Testing Library depende de `afterEach` estar em `globalThis`
 * (checagem interna da lib), o que não é o caso aqui. Sem isso, testes que não
 * navegam para longe do próprio form (ex.: um teste de validação que mantém o
 * mesmo form montado) deixam elementos "presos" no DOM entre `it()`s do mesmo
 * arquivo, quebrando qualquer query que dependa de "o único form" na página.
 * `clearAllMocks` (não `resetAllMocks`) zera só o histórico de chamadas — a
 * implementação inicial de um mock (`vi.fn(async () => ...)` no factory de
 * `vi.mock`, usada por mais de um teste sem reconfigurar) continua de pé.
 */
afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

// next-themes (enableSystem) reads matchMedia to detect the OS theme; jsdom doesn't implement it.
window.matchMedia ??= (query: string) =>
  ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  }) as unknown as MediaQueryList;

// Radix `Select` (usado por filtros de papel/status/prioridade em toda a UI de
// administração/toolbars) chama essas APIs de ponteiro ao abrir/fechar via clique
// — jsdom não as implementa, e sem isso qualquer teste que clique um `Select`
// lança `target.hasPointerCapture is not a function`.
Element.prototype.hasPointerCapture ??= () => false;
Element.prototype.setPointerCapture ??= () => {};
Element.prototype.releasePointerCapture ??= () => {};
Element.prototype.scrollIntoView ??= () => {};

// `cmdk` (command palette) observa o tamanho da lista via ResizeObserver, que
// jsdom não implementa — sem isso, montar `CommandPalette` lança
// `ResizeObserver is not defined`.
class ResizeObserverStub {
  observe() {}
  unobserve() {}
  disconnect() {}
}
window.ResizeObserver ??= ResizeObserverStub as unknown as typeof ResizeObserver;
