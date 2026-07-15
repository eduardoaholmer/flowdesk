# Buttons

Primitivo: `ui/button.tsx` (shadcn). Não criar um segundo componente de botão —
todo botão do app é `Button` com a combinação certa de `variant`/`size`.

## Variantes

| Variant       | Uso                                                                                                                                      |
| ------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| `default`     | Ação primária da tela/seção (uma só por contexto).                                                                                       |
| `outline`     | Ação secundária.                                                                                                                         |
| `secondary`   | Ação alternativa sem ser primária nem discreta.                                                                                          |
| `ghost`       | Ação de baixa ênfase (ex.: dentro de uma linha de tabela).                                                                               |
| `destructive` | Ação irreversível/perigosa — sempre atrás de um `ConfirmActionDialog`/`DeleteDialog` (ver `dialogs.md`), nunca disparando a ação direto. |
| `link`        | Ação que parece texto.                                                                                                                   |

## Tamanhos

`default` / `xs` / `sm` / `lg` para botão com texto; `icon` / `icon-xs` / `icon-sm` /
`icon-lg` para botão só-ícone — **todo** botão só-ícone exige `aria-label` (ver
`icon.md`... `icons.md` e `ActionMenu`/`IssueRowActions`/etc. para o padrão já
estabelecido).

## Múltiplas ações relacionadas

- 2-3 ações lado a lado, ícone-only: botões inline (padrão hoje em
  `IssueRowActions`/`ProjectRowActions`/`LabelRowActions`).
- 3+ ações, ou ações com texto: `ActionMenu` (`shared/components/navigation/`) —
  dropdown genérico sobre `ui/dropdown-menu.tsx`, reservado para os casos futuros da
  Sprint 9 (ver `dropdowns.md`).
