# Colors

Fonte de verdade: `src/index.css` (`:root`/`.dark`) — nomes semânticos em
`src/shared/theme/tokens/colors.ts` (não redefine valor nenhum).

## A marca Ring Gate

A identidade é monocromática — tinta sobre papel, o mesmo par usado pela `Logo`/
favicon desde sempre:

- `--brand-ink`: `oklch(0.1864 0.008 95.48)` (`#14130F`)
- `--brand-paper`: `oklch(0.9793 0.007 88.64)` (`#FAF8F3`)

Desde o Milestone 3 (`docs/09-decision-log.md` ADR-019), esses dois pontos deixaram
de existir só na marca — toda a paleta semântica (`background`, `foreground`,
`primary`, `card`, `popover`, `border`, `ring`, `sidebar-*`...) é uma rampa de neutros
quentes derivada deles: mesmo matiz (~90–92°), croma baixo (~0.006–0.02) em toda a
escala. **Nenhuma cor nova foi inventada** — é a mesma tinta/papel já aprovados,
estendidos para toda superfície semântica em vez de só o logotipo.

## O que não é marca

`--destructive` é vermelho puro nos dois temas, inalterado por este milestone — é
cor funcional (erro/ação irreversível), não expressão de identidade visual. Manter um
vermelho reconhecível como "perigo" universalmente é mais importante aqui do que
consistência com o matiz quente do resto da paleta.

## Contraste

Todo par texto/fundo da rampa foi verificado contra WCAG 2.1 (cálculo de luminância
relativa a partir do OKLCH convertido para sRGB) antes de ser aplicado:

| Par                                        | Claro  | Escuro |
| ------------------------------------------ | ------ | ------ |
| `foreground`/`background`                  | 17.5:1 | 18.3:1 |
| `primary-foreground`/`primary`             | 17.6:1 | 14.7:1 |
| `muted-foreground`/`background`            | 5.65:1 | 7.8:1  |
| `ring`/`background` (não-texto, alvo ≥3:1) | 3.72:1 | 4.53:1 |
| `text-destructive`/`background`            | 5.3:1  | 6.71:1 |

`--destructive` em modo claro foi escurecido de `oklch(0.577 ...)` (herdado do
scaffold shadcn, 4.49:1 — abaixo do mínimo AA de 4.5:1 para texto) para
`oklch(0.52 ...)` durante este milestone, mesma matiz/croma, só mais escuro o
suficiente para folga real acima do mínimo.

## O que não mudou

`chart-*` e `sidebar-*` (8 variáveis cada, ×2 temas) não têm nenhum consumidor real
hoje (`ui/sidebar.tsx` do shadcn nunca foi adotado — `layout/Sidebar.tsx` é
inteiramente próprio; nenhuma feature de gráfico existe ainda). Retintados para a
mesma rampa por consistência/baixo custo (só CSS custom properties, não uma
dependência), não removidos — se um consumidor real aparecer (`ui/sidebar.tsx`
shadcn, um gráfico futuro), já nascem no tom certo.

## Tokens finos do Milestone 7 (redesign, ADR-044)

O handoff de design em `docs/design-handoff/2026-07-20-redesign-gestor/` (README +
protótipos `.dc.html`) especifica uma paleta mais fina do que a rampa semântica atual
cobre — oito tokens novos, valores hexadecimais literais do handoff (não derivados
matematicamente da rampa ink/paper, ao contrário de `background`/`foreground`/etc.):

| Token       | Uso pretendido                              | Claro     | Escuro    |
| ----------- | ------------------------------------------- | --------- | --------- |
| `--panel`   | cards/modais/popovers, distinto de `--card` | `#FFFDF8` | `#1C1A14` |
| `--sunken`  | hover, skeleton, trilha de progresso        | `#F1EDE1` | `#262319` |
| `--t2`      | texto secundário (2º nível da hierarquia)   | `#575246` | `#B8B1A0` |
| `--t3`      | texto terciário/placeholder (3º nível)      | `#78715F` | `#918A78` |
| `--border2` | borda em hover/foco, inputs                 | `#D5CEBC` | `#3C382A` |
| `--redbg`   | fundo de alerta de erro                     | `#F8ECEA` | `#2C1613` |
| `--amber`   | status "Em andamento"/"Em revisão"          | `#8F6A11` | `#D9A73C` |
| `--green`   | status "Concluída"                          | `#50713A` | `#96B471` |

O handoff também define `--bg`/`--text`/`--red`, que **não** viraram tokens novos —
mapeiam diretamente para `--background`/`--foreground`/`--destructive` já existentes
(evita duplicar o mesmo valor sob dois nomes). `--panel`/`--sunken`/`--redbg` ainda
não têm consumidor real (primeiro uso é `IssueStatusIcon`/`IssuePriorityIcon` para
`--amber`/`--green`/`--t2`/`--t3`/`--border2` — as sub-sprints seguintes de M7
adotam os demais ao redesenhar cada tela) — mesmo precedente de `chart-*`/`sidebar-*`
acima: preparados de uma vez por baixo custo, adotados incrementalmente.
