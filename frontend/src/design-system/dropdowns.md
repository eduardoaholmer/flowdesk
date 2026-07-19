# Dropdowns

Primitivo: `ui/dropdown-menu.tsx` (Radix `DropdownMenu`, animação `data-open`/
`data-closed` com `--duration-fast`, `ring-1 ring-foreground/10` — mesmo tratamento de
elevação de `ui/dialog.tsx`/`ui/select.tsx`, ver `elevation.md`/`shadow.md`).

## Call sites reais

- `shared/components/layout/Sidebar.tsx` (`WorkspaceSwitcher`) — troca de workspace,
  `DropdownMenuItem` simples + `DropdownMenuLabel`/`Separator`.
- `shared/components/ThemeToggle.tsx` — Claro/Escuro/Sistema.
- `shared/components/layout/Topbar.tsx` — menu de usuário/notificações.
- `features/labels/components/IssueLabelPicker.tsx` — único consumidor de
  `DropdownMenuCheckboxItem` hoje: aplicar/remover labels de uma issue sem fechar o
  menu a cada clique (multi-seleção via toggle, não navegação).
- `shared/components/navigation/ActionMenu.tsx` — casca genérica (`items` + ícone
  `MoreHorizontal`) para menu de ações "⋮" quando uma linha tem 3+ ações. Preparado na
  Sprint 8.5, **ainda sem call site**: `IssueRowActions`/`ProjectRowActions`/
  `LabelRowActions` continuam com botões de ícone lado a lado (editar/excluir, 2 ações),
  que não justificam um menu — usar `ActionMenu` no dia em que uma dessas linhas
  ganhar uma 3ª ação (ver plano da Sprint 8.8/8.9 referenciado no próprio componente).

## Dropdown vs. Select

`ui/dropdown-menu.tsx` é para **ação** (algo acontece ao clicar um item — navegar,
alternar tema, aplicar uma label). `ui/select.tsx` (Radix `Select`) é para **escolher um
valor de formulário** (status/prioridade/projeto/responsável em
`IssueFormFields`/`ProjectFormFields`) — mesmo look (`ring-1 ring-foreground/10`,
`shadow-md`, animação idêntica), papel diferente. Nenhum formulário deste app usa
`DropdownMenu` para captura de valor, e nenhuma ação usa `Select`.

## Menu vs. Dialog

Um `DropdownMenuItem` nunca abre um formulário inline — quando a ação precisa de mais
input que um clique (editar, excluir com confirmação), o item de menu é só o gatilho
para um `Dialog`/`AlertDialog` (ver `dialogs.md`). Hoje isso não aparece em nenhum
dropdown real do app porque `IssueRowActions` etc. ainda não usam `ActionMenu` — é o
padrão a seguir quando um desses ganhar itens que abrem diálogo.
