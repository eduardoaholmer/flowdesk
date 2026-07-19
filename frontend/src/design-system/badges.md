# Badges

Primitivo: `ui/badge.tsx` (`cva`, variantes `default`/`secondary`/`destructive`/`outline`/
`ghost`/`link`). Nenhuma feature usa `Badge` cru diretamente para status de domínio —
cada domínio tem seu próprio wrapper fino que resolve o mapeamento enum → label/variante,
e `Badge` nunca reimplementa essa regra:

- `features/issues/components/IssueStatusBadge.tsx` — status da issue, sobre `Badge`
  (mapeia cada `IssueStatus` para uma `variant` fixa: `outline` para `Backlog`/`Todo`,
  `secondary` para `In Progress`/`In Review`, `default` para `Done`, `destructive` para
  `Canceled`).
- `features/issues/components/IssuePriorityBadge.tsx` — prioridade. **Não** usa
  `ui/badge.tsx` apesar do nome — é um `<span>` com ícone + texto, sem pílula de fundo
  (`Minus`/`ChevronsDown`/`ChevronDown`/`ChevronsUp`/`AlertTriangle` conforme a
  prioridade). Distinção intencional observada na Sprint 13.4: prioridade é
  hierárquica/escalar (a série de ícones já comunica ordem), status é categórico — só o
  categórico ganha pílula colorida.
- `features/projects/components/ProjectStatusBadge.tsx` — status do projeto, sobre
  `Badge`.
- `features/labels/components/LabelBadge.tsx` — label de usuário (cor arbitrária vinda
  do dado, não de uma variante fixa do design system — ver `colors.md` sobre cor
  arbitrária de domínio vs. paleta do tema).

`shared/components/data-display/StatusBadge.tsx` generaliza o mesmo padrão (`label` +
`variant` + `icon` opcional) para consumidores futuros que não sejam issue/projeto —
existe desde a Sprint 9 sem call site ainda (mesmo status de outros componentes
preparados na Sprint 8.5, ver `README.md`); não substitui os wrappers específicos
acima, que continuam donos do próprio mapeamento.

## Convenção de variante por semântica

Não há uma tabela fixa "status X → variante Y" centralizada — cada wrapper decide, mas
o vocabulário de `variant` é consistente em todo o app:

- `destructive` — estado terminal negativo (`Canceled`, prioridade `Urgent`).
- `secondary`/`outline` — neutro (`Backlog`, `Todo`, `No priority`).
- `default` — estado ativo/em progresso ou o item primário de uma lista.

## Composição

`Badge` aceita ícone como filho direto (`<Icon />` antes do texto) — o CSS já reserva o
espaço (`has-data-[icon=inline-start]:pl-1.5`), nenhum wrapper precisa de margin manual.
`asChild` (via `radix-ui` `Slot`) existe para o caso raro de um badge clicável/link, não
usado hoje.
