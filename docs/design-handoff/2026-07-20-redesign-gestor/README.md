# Handoff: FlowDesk — Gestor de Issues (redesign estilo Linear)

## Overview
FlowDesk é uma ferramenta de gestão de trabalho (issues + projetos) para times de produto/engenharia de 5–50 pessoas, sob a identidade própria **Ring Gate**. Este pacote entrega o protótipo navegável completo: autenticação, dashboard, issues (lista/board/detalhe), projetos, labels e administração de workspace, em light e dark mode.

## Sobre os arquivos de design
Os arquivos `.dc.html` deste pacote são **protótipos de referência em HTML** — mostram visual, copy, estados e comportamento pretendidos, mas não são código de produção para copiar diretamente. A tarefa é **recriar estas telas no ambiente real do produto** (o stack/framework já usado no repositório de destino — React, Vue etc. — ou, se ainda não existir um, escolher o mais adequado) usando os padrões de componentização, roteamento e gerenciamento de estado já estabelecidos ali.

## Fidelidade
**Alta fidelidade (hifi)**: cores, tipografia, espaçamento e microinterações finais. Recrie pixel a pixel usando as bibliotecas/padrões do codebase de destino.

## Identidade de marca (Ring Gate) — não é sugestão, é especificação
- **Símbolo**: um anel (círculo, traço grosso ~2.4px) atravessado por duas barras verticais curtas (uma acima, uma abaixo do centro) — ver `<svg>` no topo da Sidebar e da tela de Autenticação.
- **Paleta**: monocromática, quente. Dois pontos travados:
  - Ink (quase-preto quente): `#14130F`
  - Paper (quase-branco quente): `#FAF8F3`
  - Toda a rampa de neutros deriva desses dois pontos (nunca cinza puro/frio).
  - Vermelho puro é a única cor fora da marca, reservada a estados destrutivos/erro.
- **Tipografia**: Geist Variable (corpo, sans) + Fraunces Variable (títulos, serif de exibição). Contraste sans/serif intencional.
- **Tom**: editorial, contido, whitespace generoso. Sem gradientes, sem glassmorphism.
- **Contraste**: WCAG 2.1 AA (texto ≥4.5:1, elementos não-texto ≥3:1) — verificado nos tokens abaixo, inclusive no dark mode (o badge de prioridade "Média" foi corrigido para ≥3:1 — ver issue FD-10 nos dados de exemplo).

## Design tokens

### Cores (custom properties, definidas em `:root` e `[data-theme="dark"]` no `<style>` de cada arquivo)
Light:
```
--bg:#FAF8F3        fundo da página
--panel:#FFFDF8     cards, modais, popovers
--sunken:#F1EDE1    hover, skeleton, trilhas de progresso
--text:#14130F      texto primário
--t2:#575246        texto secundário
--t3:#78715F        texto terciário / placeholder
--border:#E7E1D2    bordas sutis (divisores)
--border2:#D5CEBC   bordas em foco/hover, inputs
--red:#C0271C       erro/destrutivo
--redbg:#F8ECEA     fundo de alerta de erro
--amber:#8F6A11     status "em andamento" (light)
--green:#50713A     status "concluída" (light)
--sh:0 12px 32px rgba(20,19,15,.10)   sombra de popover/modal
```
Dark:
```
--bg:#14130F  --panel:#1C1A14  --sunken:#262319
--text:#FAF8F3  --t2:#B8B1A0  --t3:#918A78
--border:#2B2820  --border2:#3C382A
--red:#F0685E  --redbg:#2C1613
--amber:#D9A73C  --green:#96B471
--sh:0 12px 32px rgba(0,0,0,.5)
```
Tema é lido/persistido em `localStorage['fd-theme']` e aplicado via `document.documentElement.dataset.theme`.

### Tipografia
- Fonte de corpo: `'Geist', system-ui, sans-serif` — pesos 300–800, tamanho base 13.5px, line-height 1.45.
- Fonte de títulos: `'Fraunces', serif` — usada em `<h1>/<h2>/<h3>` de tela e em nomes de card/projeto; pesos entre 560–640, `letter-spacing:-.01em`.
- Import via Google Fonts: `Fraunces:opsz,wght@9..144,300..800` + `Geist:wght@300..800`.
- Nunca usar cinza puro/frio — sempre os tokens acima.

### Espaçamento e forma
- Border-radius: 7–8px em controles pequenos, 10–12px em cards/popovers, 14px em modais, 999px em pills/badges.
- Bordas: 1px solid var(--border) por padrão; var(--border2) em hover/foco.
- Sombra única do sistema: `var(--sh)` para qualquer elemento flutuante (dropdown, popover, modal, toast).

### Linguagem visual de Status e Prioridade (não é só texto — cor + forma)
Status (círculo, ordem Backlog→Cancelada):
- Backlog: círculo vazio, borda tracejada
- Todo: círculo vazio, borda sólida
- Em andamento: círculo com "fatia" preenchida em âmbar (conic-gradient meio-preenchido)
- Concluída: círculo preenchido verde com check
- Cancelada: círculo preenchido neutro (t3) com ×

Prioridade (barras estilo equalizador, estilo Linear mas redesenhado):
- Urgente: quadrado vermelho sólido com "!"
- Alta/Média/Baixa: 3 barras verticais de alturas crescentes, preenchidas progressivamente (3/3, 2/3, 1/3 em var(--text), resto var(--border2))
- Sem prioridade: travessão cinza-terciário

Essas definições em código estão centralizadas em `data.js`, objetos `STATUS` e `PRIORITY` — reaproveitar essa fonte única ao portar para componentes reais (evita drift entre lista, board, modal e painel de detalhe).

## Telas incluídas

### 1. Autenticação (`Autenticacao.dc.html`)
Um único arquivo com 7 estados navegáveis via hash: `#login`, `#cadastro`, `#recuperar` (passo 1: pedir e-mail), `#recuperar-enviado` (passo 2: confirmação), `#redefinir` (passo 2b: nova senha), `#convite-deslogado`, `#convite-logado`.
- Cartão central 400px, logo Ring Gate + nome no topo, toggle de tema no canto.
- Login: e-mail, senha (com toggle mostrar/ocultar), link "Esqueci minha senha", erro inline, spinner no botão durante "autenticação" simulada (~800ms).
- Cadastro: nome, e-mail, senha com indicador de força (3 barras + texto).
- Fluxo de recuperação em dois passos reais (pedir e-mail → tela "verifique seu e-mail" → redefinir senha com confirmação).
- Convite: variante deslogada (formulário de criar conta pré-preenchido com o e-mail convidado) e logada (confirmação simples aceitar/recusar).
- Validações client-side: formato de e-mail, senha mínima de 8 caracteres, confirmação de senha.

### 2. Início / Dashboard (`Inicio e Issues.dc.html#inicio`)
- Saudação dinâmica (bom dia/tarde/noite) + data por extenso + resumo textual do que está no radar.
- Atalhos: "Nova issue" (abre modal), "Novo projeto" (linka para Projetos).
- Três widgets: "Minhas issues" (atribuídas ao usuário, ordenadas por prioridade), "Projetos ativos" (barra de progresso + responsável), "Atividade recente" (feed de eventos).
- Estados: skeleton de carregamento, erro com retry, vazio por widget com CTA próprio.

### 3. Issues — lista (`Inicio e Issues.dc.html#issues`)
- Toggle Lista/Board no topo.
- Busca textual, filtros multi-seleção em dropdown (Status, Prioridade, Responsável, Label) com contadores, ordenação (atualização/criação/prioridade/status), botão "Limpar".
- Linha de tabela: prioridade, status, ID, título, labels (chips), avatar do responsável, tempo relativo.
- Paginação (12 por página), estados de carregamento/erro/vazio-global/vazio-por-filtro distintos.

### 4. Issues — Board Kanban (`Inicio e Issues.dc.html#board`)
- Marcado como "Visão futura" (badge tracejado) — não implementado no produto real ainda.
- 5 colunas por status, cartões arrastáveis (drag-and-drop nativo HTML5) entre colunas, o drop dispara mudança de status + toast de confirmação.
- Coluna com destino em hover recebe highlight; coluna vazia mostra placeholder de drop.

### 5. Issues — Detalhe (`Inicio e Issues.dc.html#issue/FD-1`)
- Layout de três colunas ao estilo Linear: conteúdo central (max 720px) + rail lateral de metadados (272px).
- Conteúdo: título, corpo rich-text simulado (parágrafos, headings, listas, bloco de código), anexos, timeline de atividade, comentários com @menção destacada, composer de novo comentário com autocomplete de @menção.
- Rail: dropdowns editáveis inline para Status, Prioridade, Responsável, Projeto, Estimativa (1/2/3/5/8 pts), Vencimento (atalhos relativos) e Labels (multi-seleção com cor).
- Editar abre o mesmo modal de criação, pré-preenchido.

### 6. Modal de criar/editar issue
- Título + descrição em campos "sem moldura" (parecem parte do documento), pills de Status/Prioridade/Responsável/Projeto/Labels/Estimativa como dropdowns compactos, date picker nativo para vencimento.
- Validação: título obrigatório.

### 7. Projetos (`Projetos e Labels.dc.html#projetos`)
- Toggle Ativos/Arquivados, grid de cards (nome, key de 3 letras, descrição truncada a 2 linhas, barra de progresso, avatares de membros, data de entrega).
- Estados: skeleton, erro, vazio distinto por aba (ativos vs. arquivados).

### 8. Projetos — Detalhe (`Projetos e Labels.dc.html#projeto/p1`)
- Cabeçalho com key, nome, descrição, ações Editar/Arquivar-Restaurar.
- Faixa de metadados (líder, entrega, progresso).
- Tabela de issues vinculadas (mesmo componente de linha da lista global).

### 9. Labels (`Projetos e Labels.dc.html#labels`)
- Lista com nome (pill colorida), descrição, contagem de uso, ações Editar/Excluir.
- Edição inline expande a linha em um formulário (nome, descrição, seletor de 8 cores curadas da paleta).

### 10. Administração — Configurações (`Administracao.dc.html#configuracoes`)
- Formulário nome/slug/descrição do workspace, validação de slug (`[a-z0-9-]`), botão salvar desabilitado até haver mudança válida.
- Zona de perigo: excluir workspace com confirmação por digitação do slug (padrão "type to confirm").

### 11. Administração — Membros (`Administracao.dc.html#membros`)
- Filtro por papel (Admin/Membro/Convidado), tabela paginada (8/página), dropdown de alterar papel por linha, remover com modal de confirmação. Usuário atual não pode alterar/remover a si mesmo.

### 12. Administração — Convites (`Administracao.dc.html#convites`)
- Formulário de envio (e-mail + papel), validação de e-mail e de duplicidade, lista de pendentes com reenviar/cancelar.

### 13. Componentes compartilhados
- `Sidebar.dc.html`: navegação global colapsável (58px↔232px, estado persistido), seções Workspace/Issues/Board/Administração, menu de workspace, toggle de tema (segmented control expandido / botão único recolhido), usuário + sair.
- `NotifBell.dc.html`: sino com badge de não lidas, popover de notificações (menção/atribuição/status), marcar todas como lidas, link direto para a issue.
- `CommandPalette.dc.html`: `⌘K`/`Ctrl+K` abre busca assíncrona (debounce simulado + skeleton), navegação por teclado (setas/enter/esc), grupos Recentes/Issues/Projetos/Navegação/Ações, restaura o foco ao elemento de origem ao fechar (inclusive via clique no backdrop — ver FD-1 nos dados de exemplo, que documenta esse bug corrigido).

## Interações e comportamento
- Toda navegação principal usa `location.hash` dentro de cada arquivo (SPA hash-routing) e `<a href="Outro-Arquivo.dc.html#tela">` entre arquivos — ao portar para um app real, isso vira rotas de verdade (React Router, etc.).
- Atalho de teclado global `C` cria uma nova issue (quando não há foco em input/textarea).
- Toda mutação (mudar status/prioridade, mover cartão, criar/editar issue ou projeto, convidar, remover membro) atualiza o estado local e dispara um toast de confirmação — sem chamada de rede real (mockado).
- Dropdowns/menus fecham ao clicar fora (listener em `mousedown` fora do elemento) e ao pressionar Esc quando é modal.
- Skeletons (não spinners) representam carregamento; erro sempre com botão "Tentar novamente"; vazio sempre com CTA de próxima ação — nunca só texto cinza.

## Gerenciamento de estado (para recriar)
- Fonte de dados única mockada em `data.js` (usuários, projetos, labels, issues, notificações, convites, atividade) — ao portar, isso vira chamadas a API real, mas os *shapes* de dado (campos de cada entidade) podem ser reaproveitados como contrato inicial.
- Cada tela mantém estado local de: fase (carregando/pronto/erro/vazio — controlável via prop `estadoDados` nas versões DC, para demonstração), filtros, ordenação, paginação, modal aberto, menu de dropdown aberto.
- Tema (claro/escuro) e colapso da sidebar persistem em `localStorage` (`fd-theme`, `fd-sb`); notificações lidas em `fd-nread`; recentes do command palette em `fd-rec`.

## Assets
Nenhuma imagem/ícone externo — todos os ícones são SVG inline desenhados à mão (stroke-based, 1.4–1.7px, arredondados) seguindo o mesmo vocabulário do símbolo Ring Gate. Fontes via Google Fonts (Geist, Fraunces).

## Arquivos deste pacote
- `Autenticacao.dc.html` — login, cadastro, recuperação de senha (2 etapas), aceite de convite (logado/deslogado)
- `Inicio e Issues.dc.html` — dashboard, lista de issues, board kanban, detalhe de issue, modal de criar/editar
- `Projetos e Labels.dc.html` — lista/detalhe de projetos, gestão de labels
- `Administracao.dc.html` — configurações do workspace, membros, convites
- `Sidebar.dc.html`, `NotifBell.dc.html`, `CommandPalette.dc.html` — componentes globais reutilizados por todas as telas acima
- `data.js` — dados de exemplo (workspace fictício "Vela Labs") e definições centrais de Status/Prioridade/formatação de data

Observação técnica: os arquivos `.dc.html` usam uma sintaxe de template proprietária do ambiente de design (`{{ }}`, `<sc-if>`, `<sc-for>`, `<dc-import>`) — não é HTML/JS padrão. Trate-os como especificação de layout, copy, dados e comportamento; a implementação real deve ser feita com os componentes/padrões do framework de destino, lendo a lógica de cada `class Component extends DCLogic` como pseudocódigo do comportamento esperado.
