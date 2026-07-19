# Dialogs

Dois primitivos, papéis diferentes — nenhum dos dois substitui o outro:

- `ui/dialog.tsx` (Radix `Dialog`) — formulário/conteúdo dentro de um modal. Overlay
  `bg-black/10` com `backdrop-blur-xs` (quando suportado), `DialogContent` com
  `ring-1 ring-foreground/10` (mesma elevação de `dropdown-menu.tsx`/`select.tsx`).
  `DialogFooter` tem fundo `bg-muted/50` + `border-t` — separa visualmente a ação do
  corpo do formulário; nenhum outro overlay deste app usa esse tratamento de footer.
- `ui/alert-dialog.tsx` (Radix `AlertDialog`) — confirmação de uma ação, nunca contém
  formulário. Sempre acessado através de `shared/components/overlay/
ConfirmActionDialog.tsx` (`title`/`description`/`confirmLabel`/`destructive`/
  `onConfirm`/`isPending`) — nenhuma feature monta `AlertDialog` cru, todas passam por
  esse wrapper. `overlay/DeleteDialog.tsx` é um preset de `ConfirmActionDialog`
  (`confirmLabel="Excluir"` + `destructive` fixos) pensado para o caso mais comum do
  app — **ainda sem call site**: `IssueRowActions`/`ProjectRowActions`/
  `LabelRowActions` chamam `ConfirmActionDialog` diretamente com os mesmos parâmetros
  ao invés do preset (inconsistência observada na Sprint 13.4, não bloqueante — trocar
  pelo preset é um follow-up de baixo risco, não uma correção de bug).

## Padrão de formulário em `Dialog` (create/edit)

`CreateIssueDialog`/`EditIssueDialog`, `CreateProjectDialog`/`EditProjectDialog`,
`CreateLabelDialog`/`EditLabelDialog` seguem o mesmo esqueleto:

```
Dialog (open/setOpen via useState local, nunca em store global)
  DialogTrigger asChild → Button (texto no create: "Novo X"; ícone de lápis no edit)
  DialogContent
    form (react-hook-form + zodResolver)
      DialogHeader → DialogTitle
      <XFormFields ...> — componente de campos compartilhado entre create/edit
      DialogFooter → Button type="submit"
```

O par create/edit de cada domínio compartilha um único `<XFormFields>` (ex.:
`IssueFormFields`) — o dialog em si só monta `useForm`, resolve `defaultValues`
(create) ou `values` controlados pela entidade (edit, via `values` do RHF — não
`defaultValues`, para reagir se a entidade mudar sob o dialog aberto) e chama o mutation
certo no `onSubmit`. Nenhum campo é reimplementado entre create e edit.

## Confirmado na revisão visual da Sprint 13.4

Abrir um `Select` (Status/Prioridade/Projeto/Responsável de `IssueFormFields`) dentro de
um `Dialog` aberto funciona corretamente — cliques chegam ao trigger certo, sem
interceptação pelo overlay. (Suspeita inicial de bug descartada após inspecionar
`document.elementFromPoint` em navegador real: o elemento que parecia "bloqueado" em um
teste automatizado inicial era, na verdade, um controle da página por trás do modal,
corretamente coberto pelo overlay — comportamento esperado de qualquer modal.)
