# Elevation

"Elevação" combina duas dimensões que respondem perguntas diferentes:

- **Sombra** (`shadow.md`) — responde "isto parece estar acima do plano da página?"
  (sinal visual).
- **Z-index** (`src/shared/theme/tokens/zIndex.ts`, `zIndexTokens`/`layers`) —
  responde "isto realmente está acima, na ordem de empilhamento real do navegador?"
  (mecânica de stacking).

## Camadas (`layers`)

```ts
export const zIndexTokens = {
  dropdown: 20,
  sticky: 30,
  overlay: 40,
  modal: 50,
  popover: 60,
  toast: 70,
} as const;
```

**Importante**: isto é só para overlays _customizados_ do app (ex.: um sticky header
próprio, um drawer que não seja `ui/sheet.tsx`). As primitivas Radix/shadcn
(`Dialog`/`Popover`/`DropdownMenu`/`Sheet`/`Tooltip`) já gerenciam seu próprio
empilhamento via portal + `z-50` interno (ver `dropdown-menu.tsx`) — nunca sobrescreva
o z-index de um primitivo Radix com um valor de `layers`, os dois não são o mesmo
mecanismo. Use `layers` apenas em CSS/inline `style` de elemento que **você** está
posicionando com `position: sticky/fixed` fora de um primitivo Radix (ex.: `Topbar`
sticky, `Sidebar` mobile drawer antes de virar `Sheet`).
