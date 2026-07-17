# Motion

CSS-only (Milestone 3, `docs/09-decision-log.md` ADR-019) — sem framer-motion, sem
biblioteca de animação JS. Fonte de verdade dos valores:
`src/shared/theme/tokens/motion.ts` (referência tipada) / `src/index.css` (`--duration-*`/`--ease-*`, os valores reais).

```ts
export const motionTokens = { duration: { fast, base, slow }, easing: { standard, emphasized } };
// fast = 100ms, base = 150ms, slow = 250ms
// standard = cubic-bezier(0.4, 0, 0.2, 1) — a maioria das transições
// emphasized = cubic-bezier(0.2, 0, 0, 1) — entrada de algo que precisa de mais atenção (raro)
```

## Onde a animação vem de graça

Todo overlay do projeto (`Dialog`/`AlertDialog`/`Sheet`/`DropdownMenu`/`ContextMenu`/
`Popover`/`HoverCard`/`Select`) é Radix + `tw-animate-css`: a transição de abrir/fechar
já vem das classes `data-open:animate-in`/`data-closed:animate-out` + `fade-*`/`zoom-*`/
`slide-*`, disparadas pelo próprio atributo `data-state` do Radix — nenhum componente
precisa (nem deve) orquestrar isso manualmente. A duração dessas classes referencia os
tokens diretamente na className (`duration-[var(--duration-fast)]`), não um valor
hardcoded — é o único lugar onde `--duration-*` realmente é consumido.

## Onde `transition-*` do Tailwind já cobre o resto

Hover/focus de botão, linha de tabela, item de menu — tudo já usa `transition-colors`/
`transition-all` do Tailwind (ver `ui/button.tsx`, `ui/table.tsx`, `layout/Sidebar.tsx`)
com a duração default do Tailwind (curta o bastante para não precisar de um token
próprio). Não introduza uma segunda forma de fazer a mesma coisa.

## Por que não uma biblioteca de animação JS

O projeto teve `framer-motion` instalado (Sprint 8.8/8.9, nunca documentada em
`docs/08-roadmap.md` — divergência encontrada na auditoria do Milestone 3) com 10
componentes wrapper (`FadeIn`, `FadeUp`, `MotionCard`, `MotionPage`, etc.). Nenhum
teve um único call site real em nenhuma tela do produto. Removido no Milestone 3:
zero valor entregue, custo real de bundle, e — mais importante — filosoficamente
oposto ao motion system que este produto quer ("Linear, Raycast, Vercel": rápido,
sem espera por uma animação de saída antes da próxima tela carregar). CSS-only não é
uma limitação, é a escolha certa para "prioritize speed" — não há JS no caminho
crítico de abrir um dropdown ou navegar de página.

## Princípio geral

"Discreto, nada exagerado": durações de 100–250ms, nunca bounce/spring chamativo. Se
uma transição chama mais atenção que o conteúdo que ela revela, está forte demais.

## Acessibilidade

`@media (prefers-reduced-motion: reduce)` em `src/index.css` zera duração de toda
animação/transição do projeto de uma vez (uma regra global, não uma flag por
componente) — cobre `data-state` do Radix, `transition-*` do Tailwind e
`animate-spin`/`animate-pulse` sem exigir tratamento individual em cada um.
