# Radius

Fonte de verdade: `src/shared/theme/tokens/radius.ts` (`radiusTokens`) e `--radius`
(`src/index.css`, `0.625rem`) — todo `--radius-*` é derivado dela em `@theme inline`:

```css
--radius-sm: calc(var(--radius) * 0.6);
--radius-md: calc(var(--radius) * 0.8);
--radius-lg: var(--radius);
--radius-xl: calc(var(--radius) * 1.4);
--radius-2xl: calc(var(--radius) * 1.8);
--radius-3xl: calc(var(--radius) * 2.2);
--radius-4xl: calc(var(--radius) * 2.6);
```

Uma única variável (`--radius`) controla a "personalidade" de todo o app — mudar o
raio-base da marca definitiva é uma linha em `index.css`, não uma varredura de
componente por componente.

## Uso já estabelecido

`Card`/`Dialog`/`Sheet`/`Popover`/`DropdownMenu` usam `rounded-xl`/`rounded-lg`
internamente (shadcn default). `Badge` usa `rounded-4xl` (pill). Novos componentes
compostos devem herdar o raio do primitivo shadcn que envolvem, não declarar um
`rounded-*` próprio.
