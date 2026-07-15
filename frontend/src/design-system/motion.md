# Motion

Instalado na Sprint 8.8/8.9 (`framer-motion`, antes ausente do projeto). Fonte de
verdade dos valores: `src/shared/theme/tokens/motion.ts`.

```ts
export const motionTokens = { duration: { fast, base, slow }, easing: { standard, emphasized } }; // CSS vars, para className
export const motionDurationSeconds = { fast: 0.1, base: 0.15, slow: 0.25 }; // números, para Framer Motion
export const motionEasing = { standard: [0.4, 0, 0.2, 1], emphasized: [0.2, 0, 0, 1] };
```

`motionDurationSeconds`/`motionEasing` espelham manualmente `--duration-*`/`--ease-*`
de `index.css` — Framer Motion não lê custom properties CSS como duração/curva,
só números, então os dois precisam ser mantidos em sincronia se `index.css` mudar.

## Componentes (`shared/components/motion/`)

`FadeIn`, `FadeUp`, `FadeDown`, `ScaleIn`, `SlideLeft`, `SlideRight` — todos aceitam
`children`, `className`, `delay?` (segundos) e respeitam `prefers-reduced-motion`
automaticamente via `useReducedMotion()` (Framer Motion): quando o usuário prefere
movimento reduzido, a transição vira duração `0` e nenhum transform (`y`/`x`/`scale`)
é aplicado — só o `opacity`.

```tsx
<FadeUp delay={0.05}>
  <StatCard label="Issues abertas" value={12} />
</FadeUp>
```

### Orquestrando uma lista (`StaggerContainer`)

Todo filho direto que deve entrar em sequência (não simultaneamente) precisa de
`inherit` — sem isso, cada filho anima sozinho ao montar, ignorando o atraso do pai:

```tsx
<StaggerContainer className="flex flex-col gap-2">
  {items.map((item) => (
    <FadeUp key={item.id} inherit>
      <ItemRow item={item} />
    </FadeUp>
  ))}
</StaggerContainer>
```

### `MotionCard`

Resposta a hover/tap (`whileHover`/`whileTap`), não uma entrada — para cards
clicáveis. `whileHover`/`whileTap` são omitidos inteiramente (não só acelerados) sob
`prefers-reduced-motion`.

### `MotionModal`

Reveal de conteúdo **dentro** de um modal já aberto (ex.: trocar de etapa de um
wizard). **Não envolva `DialogContent`/`SheetContent` inteiro com isto** — o Radix já
anima abrir/fechar via `data-state` + classes Tailwind (`data-open:animate-in...`,
ver `ui/dialog.tsx`); duplicar com `MotionModal` por cima anima duas vezes ao mesmo
tempo.

### `MotionPage`

Entrada discreta de conteúdo de página. Não coordena transição de **saída** entre
rotas — isso exigiria `AnimatePresence` no nível do `router.tsx` (decisão de
arquitetura de roteamento, não implementada nesta sprint de infraestrutura).

## Princípio geral

"Discreto, nada exagerado" (pedido explícito): durações de 100–250ms, deslocamentos
de 8–16px, nunca bounce/spring chamativo. Se uma animação chama mais atenção que o
conteúdo que ela revela, está forte demais.
