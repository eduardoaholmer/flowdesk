# Badges

Primitivo: `ui/badge.tsx` (`cva`, variantes `default`/`secondary`/`destructive`/`outline`/
`ghost`/`link`). Nenhuma feature usa `Badge` cru diretamente para status de domínio —
cada domínio tem seu próprio wrapper fino que resolve o mapeamento enum → label/visual,
e `Badge` nunca reimplementa essa regra:

- `features/issues/components/IssueStatusBadge.tsx`/`IssuePriorityBadge.tsx` — status e
  prioridade da issue. **Desde o Milestone 7** (redesign, ADR-044) nenhum dos dois usa
  mais `ui/badge.tsx` — ambos compõem um glifo geométrico (`IssueStatusIcon`/
  `IssuePriorityIcon`, `<span>` com CSS inline reproduzindo o handoff de design) + o
  label em texto simples, substituindo a pílula colorida de status e os ícones lucide
  de prioridade usados até então. Ver "Linguagem visual de Status/Prioridade" abaixo —
  a distinção categórico-vs-hierárquico da Sprint 13.4 (só status ganhava pílula) foi
  superada por essa mudança: agora os dois são um glifo + texto, sem pílula.
- `features/projects/components/ProjectStatusBadge.tsx` — status do projeto, sobre
  `Badge`. Fora do escopo do redesign de M7 até aqui (handoff não cobre `Project`
  como entidade com badge própria) — continua pílula.
- `features/labels/components/LabelBadge.tsx` — label de usuário (cor arbitrária vinda
  do dado, não de uma variante fixa do design system — ver `colors.md` sobre cor
  arbitrária de domínio vs. paleta do tema).

`shared/components/data-display/StatusBadge.tsx` generaliza o mesmo padrão (`label` +
`variant` + `icon` opcional) para consumidores futuros que não sejam issue/projeto —
existe desde a Sprint 9 sem call site ainda (mesmo status de outros componentes
preparados na Sprint 8.5, ver `README.md`); não substitui os wrappers específicos
acima, que continuam donos do próprio mapeamento.

## Convenção de variante por semântica

Aplica-se hoje só a `ProjectStatusBadge` (issue status/priority migraram para glifo,
ver acima) — o vocabulário de `variant` é consistente onde `Badge` ainda é usado:

- `destructive` — estado terminal negativo.
- `secondary`/`outline` — neutro.
- `default` — estado ativo/em progresso ou o item primário de uma lista.

## Linguagem visual de Status/Prioridade (Milestone 7, ADR-044)

`IssueStatusIcon`/`IssuePriorityIcon` (`features/issues/components/`) reproduzem o
glifo especificado no handoff (`docs/design-handoff/2026-07-20-redesign-gestor/data.js`,
objetos `STATUS`/`PRIORITY`) via `<span>` com `style` inline — `conic-gradient`/
`linear-gradient` em camadas não são expressáveis como utility Tailwind, mesmo
critério já usado por `TableRow` (Sprint 13.3, `hover:shadow-[inset_...]`) para CSS que
foge do vocabulário de classes.

**Status** — círculo de 14px, ordem Backlog→Cancelada:

- Backlog: contorno tracejado `--t3`, vazio.
- Todo: contorno sólido `--t2`, vazio.
- Em andamento: contorno `--amber`, ponto interno com `conic-gradient` meio-preenchido.
- Em revisão: **extensão própria desta sprint** — o handoff só modela 5 status (não
  cobre `IN_REVIEW`, que existe no domínio real desde a Sprint 7/ADR-012). Reaproveita
  o mesmo `--amber`, fatia de 270° em vez de 180° — comunica "mais perto de concluído"
  sem inventar uma cor fora da paleta monocromática.
- Concluída: preenchido `--green`, glifo `✓`.
- Cancelada: preenchido `--t3`, glifo `×`.

**Prioridade** — "barras de equalizador" (13×11px, 3 barras em alturas 45%/72%/100%):

- Urgente: quadrado `--destructive` preenchido, glifo `!`.
- Alta: 3 barras em `--foreground`.
- Média: 2 barras em `--foreground` + 1 em `--border2`.
- Baixa: 1 barra em `--foreground` + 2 em `--border2`.
- Sem prioridade: travessão `--t3`, sem barras.

Ambos os componentes só renderizam o glifo (`aria-hidden`) — o wrapper `*Badge` é quem
compõe glifo + label em texto legível para leitor de tela. `IssueBoardCard` (Sprint
18.2) é o primeiro consumidor do glifo isolado (`IssuePriorityIcon`, sem `*Badge`) —
cartão de board é compacto de propósito, sem espaço para o label por extenso; o
próprio agrupamento por coluna já comunica o status, então o card nem renderiza
`IssueStatusIcon`. `IssuesTable` (Sprint 18.4) segue o mesmo caminho — glifo isolado
para Status/Prioridade em vez da badge com texto, densidade compatível com uma linha
de tabela — mas envolve cada ícone num `<span role="img" aria-label title>` para não
perder o rótulo acessível/hover que a badge carregava (a diferença de `IssueBoardCard`:
ali o glifo é puramente decorativo dentro de um cartão que já tem outro contexto
textual, aqui é a única indicação de status/prioridade da linha). Os widgets do Início
(`MyIssuesWidget`, Sprint 18.5) reaproveitam o mesmo par de ícones sem o wrapper de
acessibilidade — linha inteira é um link para a issue, cujo `title`/conteúdo já dá
contexto.

## Composição

`Badge` aceita ícone como filho direto (`<Icon />` antes do texto) — o CSS já reserva o
espaço (`has-data-[icon=inline-start]:pl-1.5`), nenhum wrapper precisa de margin manual.
`asChild` (via `radix-ui` `Slot`) existe para o caso raro de um badge clicável/link, não
usado hoje.
