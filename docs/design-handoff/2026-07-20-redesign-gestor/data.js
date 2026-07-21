// FlowDesk — dados fictícios do workspace Vela Labs
export const WORKSPACE = { name: 'Vela Labs', slug: 'vela-labs' };

export const USERS = [
  { id: 'u1', name: 'Marina Costa', email: 'marina@velalabs.com.br', ini: 'MC', role: 'Admin', since: '2025-09-02' },
  { id: 'u2', name: 'Rafael Duarte', email: 'rafael@velalabs.com.br', ini: 'RD', role: 'Admin', since: '2025-09-02' },
  { id: 'u3', name: 'Beatriz Nogueira', email: 'beatriz@velalabs.com.br', ini: 'BN', role: 'Membro', since: '2025-10-14' },
  { id: 'u4', name: 'Thiago Lima', email: 'thiago@velalabs.com.br', ini: 'TL', role: 'Membro', since: '2025-11-03' },
  { id: 'u5', name: 'Camila Farias', email: 'camila@velalabs.com.br', ini: 'CF', role: 'Membro', since: '2026-01-12' },
  { id: 'u6', name: 'Otávio Reis', email: 'otavio@velalabs.com.br', ini: 'OR', role: 'Membro', since: '2026-01-26' },
  { id: 'u7', name: 'Lívia Antunes', email: 'livia@velalabs.com.br', ini: 'LA', role: 'Membro', since: '2026-02-09' },
  { id: 'u8', name: 'Pedro Sales', email: 'pedro@velalabs.com.br', ini: 'PS', role: 'Convidado', since: '2026-03-02' },
  { id: 'u9', name: 'Helena Prado', email: 'helena@velalabs.com.br', ini: 'HP', role: 'Membro', since: '2026-03-18' },
  { id: 'u10', name: 'Gustavo Meireles', email: 'gustavo@velalabs.com.br', ini: 'GM', role: 'Membro', since: '2026-04-06' },
  { id: 'u11', name: 'Sofia Albuquerque', email: 'sofia@velalabs.com.br', ini: 'SA', role: 'Convidado', since: '2026-05-11' },
  { id: 'u12', name: 'Daniel Rocha', email: 'daniel@velalabs.com.br', ini: 'DR', role: 'Membro', since: '2026-06-01' }
];
export const ME = USERS[0];

export const LABELS = [
  { id: 'l1', name: 'bug', color: '#B3543E', desc: 'Comportamento incorreto em produção' },
  { id: 'l2', name: 'melhoria', color: '#6B7F4A', desc: 'Refinamento de algo que já existe' },
  { id: 'l3', name: 'dívida técnica', color: '#A8842C', desc: 'Custo de decisões passadas a pagar' },
  { id: 'l4', name: 'design', color: '#8D6A96', desc: 'Precisa de definição visual ou de UX' },
  { id: 'l5', name: 'infra', color: '#4E7D74', desc: 'Deploy, observabilidade, banco' },
  { id: 'l6', name: 'docs', color: '#7C7668', desc: 'Documentação interna ou pública' }
];
export const LABEL_PALETTE = ['#B3543E', '#6B7F4A', '#A8842C', '#8D6A96', '#4E7D74', '#7C7668', '#946B4F', '#5E7D9A'];

export const PROJECTS = [
  { id: 'p1', key: 'ONB', name: 'Onboarding v2', desc: 'Reduzir o tempo até a primeira issue criada para menos de 2 minutos.', status: 'ativo', lead: 'u2', target: '2026-08-28', members: ['u2', 'u3', 'u7'] },
  { id: 'p2', key: 'PAL', name: 'Command palette', desc: 'Busca assíncrona, ações recentes e troca de workspace via ⌘K.', status: 'ativo', lead: 'u1', target: '2026-08-14', members: ['u1', 'u4', 'u9'] },
  { id: 'p3', key: 'NOT', name: 'Notificações em tempo real', desc: 'Menções, atribuições e mudanças de status sem F5.', status: 'ativo', lead: 'u5', target: '2026-09-18', members: ['u5', 'u6', 'u10'] },
  { id: 'p4', key: 'BIL', name: 'Migração de billing', desc: 'Sair do provedor atual sem downtime nem cobrança duplicada.', status: 'ativo', lead: 'u4', target: '2026-10-02', members: ['u4', 'u12'] },
  { id: 'p5', key: 'KAN', name: 'Board Kanban', desc: 'Visão por status com drag-and-drop — próximo grande milestone.', status: 'ativo', lead: 'u3', target: '2026-11-06', members: ['u3', 'u7', 'u8'] },
  { id: 'p6', key: 'DSI', name: 'Design system interno', desc: 'Componentes Ring Gate documentados e versionados.', status: 'arquivado', lead: 'u1', target: '2026-04-10', members: ['u1', 'u7'] },
  { id: 'p7', key: 'AUD', name: 'Auditoria de acessos', desc: 'Trilha de auditoria por workspace para o plano Business.', status: 'arquivado', lead: 'u2', target: '2026-03-20', members: ['u2'] }
];

export const ISSUES = [
  { id: 'FD-1', title: 'Command palette não restaura o foco ao fechar com Esc', status: 'in_progress', priority: 'high', assignee: 'u1', labels: ['l1'], project: 'p2', estimate: 3, due: '2026-07-24', created: '2026-07-15T10:20:00', updated: '2026-07-18T09:10:00',
    desc: [
      { t: 'p', x: 'Ao fechar a command palette com Esc, o foco deveria voltar para o elemento que a abriu. Hoje ele cai no body, o que quebra a navegação por teclado e falha o critério 2.4.3 (Focus Order) do WCAG.' },
      { t: 'h', x: 'Como reproduzir' },
      { t: 'li', x: 'Abra a palette com ⌘K a partir do botão de busca da topbar' },
      { t: 'li', x: 'Pressione Esc' },
      { t: 'li', x: 'Pressione Tab — o foco recomeça do início do documento' },
      { t: 'h', x: 'Comportamento esperado' },
      { t: 'p', x: 'Guardar document.activeElement na abertura e restaurar no fechamento, inclusive quando a palette é fechada por clique no backdrop.' },
      { t: 'code', x: 'const prev = document.activeElement;\n// ao fechar:\nprev?.focus({ preventScroll: true });' }
    ],
    comments: [
      { who: 'u2', when: '2026-07-17T14:30:00', text: 'Consigo reproduzir no Safari também. @Marina Costa vale conferir se o mesmo acontece no popover de notificações — suspeito que sim.' },
      { who: 'u1', when: '2026-07-17T15:04:00', text: 'Confere, o popover tem o mesmo problema. Vou tratar os dois no mesmo PR e adicionar um teste de regressão com @Thiago Lima.' },
      { who: 'u4', when: '2026-07-18T09:10:00', text: 'Teste pronto no branch qa/focus-restore. Falta só o caso do backdrop.' }
    ],
    attachments: [{ name: 'focus-trace.mp4', size: '2,1 MB' }, { name: 'wcag-2.4.3-checklist.pdf', size: '184 KB' }],
    activity: [
      { who: 'u1', what: 'criou a issue', when: '2026-07-15T10:20:00' },
      { who: 'u1', what: 'moveu de Todo para Em andamento', when: '2026-07-16T09:00:00' },
      { who: 'u2', what: 'adicionou a label bug', when: '2026-07-16T09:12:00' }
    ] },
  { id: 'FD-2', title: 'Skeleton da lista de issues pisca em conexões rápidas', d: 'Quando a resposta chega em menos de 150ms o skeleton aparece e some, causando flash. Adicionar atraso mínimo de exibição.', status: 'todo', priority: 'medium', assignee: 'u4', labels: ['l1', 'l2'], project: 'p2', estimate: 2, due: null, created: '2026-07-10T11:00:00', updated: '2026-07-16T15:40:00' },
  { id: 'FD-3', title: 'Debounce da busca assíncrona do ⌘K (250ms)', d: 'A busca dispara a cada tecla. Debounce de 250ms com cancelamento da requisição anterior.', status: 'done', priority: 'medium', assignee: 'u9', labels: ['l2'], project: 'p2', estimate: 1, due: null, created: '2026-07-08T09:30:00', updated: '2026-07-15T10:02:00' },
  { id: 'FD-4', title: 'Empty state de Projetos sem call-to-action', d: 'A tela vazia de projetos mostra só um texto cinza. Precisa de CTA de criação e ilustração da marca.', status: 'todo', priority: 'high', assignee: 'u7', labels: ['l4'], project: 'p1', estimate: 2, due: '2026-07-29', created: '2026-07-09T14:00:00', updated: '2026-07-17T09:20:00' },
  { id: 'FD-5', title: 'Menções não disparam notificação quando o comentário é editado', d: 'Adicionar @menção ao editar um comentário existente não gera notificação para a pessoa mencionada.', status: 'backlog', priority: 'high', assignee: 'u5', labels: ['l1'], project: 'p3', estimate: 3, due: null, created: '2026-07-07T16:20:00', updated: '2026-07-14T11:30:00' },
  { id: 'FD-6', title: 'Websocket cai atrás de proxy corporativo', status: 'in_progress', priority: 'urgent', assignee: 'u6', labels: ['l1', 'l5'], project: 'p3', estimate: 5, due: '2026-07-22', created: '2026-07-11T08:15:00', updated: '2026-07-18T08:05:00',
    desc: [
      { t: 'p', x: 'Clientes atrás de proxies HTTP corporativos perdem a conexão websocket a cada ~60s e as notificações em tempo real param de chegar silenciosamente.' },
      { t: 'h', x: 'Proposta' },
      { t: 'li', x: 'Fallback automático para long-polling após 2 quedas consecutivas' },
      { t: 'li', x: 'Heartbeat de 25s (abaixo do timeout típico de 30s dos proxies)' },
      { t: 'li', x: 'Indicador discreto de reconexão na topbar' }
    ],
    comments: [{ who: 'u10', when: '2026-07-17T13:00:00', text: 'O heartbeat resolveu no ambiente da Vetra. @Otávio Reis consegue validar com o proxy da Zurich amanhã?' }],
    activity: [{ who: 'u6', what: 'criou a issue', when: '2026-07-11T08:15:00' }, { who: 'u6', what: 'moveu para Em andamento', when: '2026-07-14T10:00:00' }, { who: 'u1', what: 'alterou a prioridade para Urgente', when: '2026-07-16T17:40:00' }] },
  { id: 'FD-7', title: 'Onboarding: passo de convite pula validação de e-mail', d: 'No passo 3 do onboarding dá para enviar convite com e-mail malformado. Reusar o validador do formulário de convites.', status: 'in_progress', priority: 'high', assignee: 'u3', labels: ['l1'], project: 'p1', estimate: 2, due: '2026-07-27', created: '2026-07-12T10:45:00', updated: '2026-07-17T16:10:00' },
  { id: 'FD-8', title: 'Reordenar colunas do board com teclado', d: 'Suporte a setas + espaço para mover cartões entre colunas sem mouse.', status: 'backlog', priority: 'low', assignee: 'u8', labels: ['l2', 'l4'], project: 'p5', estimate: 5, due: null, created: '2026-07-05T09:00:00', updated: '2026-07-12T14:20:00' },
  { id: 'FD-9', title: 'Retry exponencial no envio de convites', d: 'Falhas transitórias do provedor de e-mail devem re-tentar com backoff (1s, 4s, 16s) antes de marcar como erro.', status: 'done', priority: 'medium', assignee: 'u10', labels: ['l5'], project: 'p3', estimate: 2, due: null, created: '2026-07-03T15:30:00', updated: '2026-07-14T09:45:00' },
  { id: 'FD-10', title: 'Tema escuro: contraste do badge de prioridade abaixo de 3:1', d: 'O âmbar do badge Média mede 2,6:1 sobre o fundo elevado no tema escuro. Ajustar o token para ≥3:1.', status: 'done', priority: 'high', assignee: 'u7', labels: ['l1', 'l4'], project: null, estimate: 1, due: null, created: '2026-07-06T11:10:00', updated: '2026-07-13T17:00:00' },
  { id: 'FD-11', title: 'Migrar webhooks de cobrança para o novo provedor', d: 'Mapear os 9 eventos atuais, criar handlers idempotentes e rodar em paralelo por duas semanas antes do corte.', status: 'todo', priority: 'urgent', assignee: 'u4', labels: ['l5'], project: 'p4', estimate: 8, due: '2026-08-05', created: '2026-07-13T09:20:00', updated: '2026-07-17T11:55:00' },
  { id: 'FD-12', title: 'Especificar drag-and-drop entre colunas (multi-seleção?)', status: 'in_progress', priority: 'medium', assignee: 'u3', labels: ['l4'], project: 'p5', estimate: 3, due: '2026-07-31', created: '2026-07-09T10:00:00', updated: '2026-07-16T15:22:00',
    desc: [
      { t: 'p', x: 'Antes de implementar o board precisamos decidir o comportamento de arrastar: um cartão por vez ou multi-seleção com shift/cmd?' },
      { t: 'h', x: 'Questões em aberto' },
      { t: 'li', x: 'Multi-seleção entra no MVP ou fica para depois?' },
      { t: 'li', x: 'Soltar em coluna Concluída pede confirmação quando há sub-issues abertas?' },
      { t: 'li', x: 'Auto-atribuição ao mover (ver FD-23)' }
    ],
    comments: [{ who: 'u3', when: '2026-07-16T15:22:00', text: 'Rascunho de spec no Notion. @Marina Costa e @Lívia Antunes, comentem até sexta para fecharmos o escopo do MVP.' }],
    activity: [{ who: 'u3', what: 'criou a issue', when: '2026-07-09T10:00:00' }, { who: 'u3', what: 'moveu para Em andamento', when: '2026-07-15T09:30:00' }] },
  { id: 'FD-13', title: 'Paginação da lista de membros quebra com filtro de papel', d: 'Ao filtrar por Convidado a paginação mantém o total antigo e mostra páginas vazias.', status: 'todo', priority: 'medium', assignee: 'u12', labels: ['l1'], project: null, estimate: 1, due: null, created: '2026-07-14T13:40:00', updated: '2026-07-16T10:15:00' },
  { id: 'FD-14', title: 'Documentar atalhos de teclado no guia do usuário', d: 'Tabela de atalhos (⌘K, C para nova issue, ⇧⌘P para projetos) com prints nos dois temas.', status: 'backlog', priority: 'low', assignee: 'u1', labels: ['l6'], project: null, estimate: 1, due: null, created: '2026-07-02T09:00:00', updated: '2026-07-10T16:30:00' },
  { id: 'FD-15', title: 'Cache de avatares expira cedo demais', d: 'TTL de 5 minutos gera refetch constante. Subir para 24h com invalidação por hash.', status: 'backlog', priority: 'low', assignee: 'u6', labels: ['l5'], project: null, estimate: 1, due: null, created: '2026-07-04T14:00:00', updated: '2026-07-09T11:00:00' },
  { id: 'FD-16', title: 'Prorratear cobrança na troca de plano no meio do ciclo', d: 'Upgrade no dia 12 de um ciclo de 30 deve cobrar proporcional. Definir arredondamento com o financeiro.', status: 'todo', priority: 'high', assignee: 'u1', labels: [], project: 'p4', estimate: 5, due: '2026-08-12', created: '2026-07-15T09:00:00', updated: '2026-07-17T16:40:00' },
  { id: 'FD-17', title: 'Estados de erro do formulário de nova issue', d: 'Título vazio, estimativa inválida e falha de rede precisam de mensagens específicas — não um alert genérico.', status: 'done', priority: 'medium', assignee: 'u7', labels: ['l4'], project: 'p1', estimate: 2, due: null, created: '2026-06-28T10:20:00', updated: '2026-07-11T15:10:00' },
  { id: 'FD-18', title: 'Telemetria: tempo até a primeira issue criada', d: 'Medir do signup até a primeira issue. Meta do Onboarding v2: mediana < 2 min.', status: 'in_progress', priority: 'medium', assignee: 'u2', labels: ['l2'], project: 'p1', estimate: 3, due: '2026-08-03', created: '2026-07-08T11:30:00', updated: '2026-07-17T14:25:00' },
  { id: 'FD-19', title: 'Board: coluna Cancelada colapsada por padrão', d: 'Cancelada raramente interessa no dia a dia; iniciar colapsada com contador visível.', status: 'backlog', priority: 'none', assignee: 'u8', labels: ['l2'], project: 'p5', estimate: 1, due: null, created: '2026-07-06T16:00:00', updated: '2026-07-08T09:40:00' },
  { id: 'FD-20', title: 'Importador do Linear trava com mais de 2 mil issues', d: 'Importação síncrona estoura timeout. Mover para fila com progresso incremental e retomada.', status: 'todo', priority: 'urgent', assignee: 'u10', labels: ['l1', 'l5'], project: null, estimate: 8, due: '2026-07-30', created: '2026-07-16T08:50:00', updated: '2026-07-18T07:30:00' },
  { id: 'FD-21', title: 'Revisar copy do e-mail de redefinição de senha', d: 'Tom atual é robótico. Alinhar com a voz da marca: direto, caloroso, sem jargão.', status: 'todo', priority: 'low', assignee: 'u1', labels: ['l6'], project: null, estimate: 1, due: '2026-07-25', created: '2026-07-12T15:00:00', updated: '2026-07-15T09:10:00' },
  { id: 'FD-22', title: 'Dívida: remover flag antiga de dark mode', d: 'A flag ff_dark_v1 está 100% ligada há 3 meses. Remover flag e código morto.', status: 'done', priority: 'low', assignee: 'u9', labels: ['l3'], project: null, estimate: 1, due: null, created: '2026-06-30T10:00:00', updated: '2026-07-09T13:20:00' },
  { id: 'FD-23', title: 'Auto-atribuição ao mover cartão no board', d: 'Quem arrasta um cartão sem responsável para Em andamento vira o responsável — com undo no toast.', status: 'backlog', priority: 'medium', assignee: 'u3', labels: ['l2'], project: 'p5', estimate: 2, due: null, created: '2026-07-10T09:30:00', updated: '2026-07-13T10:50:00' },
  { id: 'FD-24', title: 'Notificação duplicada ao ser mencionado no próprio comentário', d: 'Mencionar a si mesmo gera notificação. Suprimir menção do próprio autor.', status: 'done', priority: 'medium', assignee: 'u5', labels: ['l1'], project: 'p3', estimate: 1, due: null, created: '2026-07-11T14:10:00', updated: '2026-07-18T08:45:00' },
  { id: 'FD-25', title: 'Slug do workspace aceita emoji no cadastro', d: 'Validação permite emoji e depois o roteamento quebra. Restringir a [a-z0-9-].', status: 'canceled', priority: 'low', assignee: 'u12', labels: ['l1'], project: null, estimate: 1, due: null, created: '2026-06-25T09:00:00', updated: '2026-07-02T10:30:00' },
  { id: 'FD-26', title: 'Trocar spinner do login por skeleton', d: 'Cancelada: o login redireciona rápido o suficiente; skeleton adicionaria complexidade sem ganho.', status: 'canceled', priority: 'none', assignee: 'u7', labels: ['l2'], project: null, estimate: 1, due: null, created: '2026-06-27T11:00:00', updated: '2026-07-05T16:00:00' }
];

export const NOTIFS = [
  { id: 'n1', type: 'mention', actor: 'u2', verb: 'mencionou você em', issue: 'FD-1', time: '2026-07-18T09:12:00', read: false },
  { id: 'n2', type: 'assign', actor: 'u2', verb: 'atribuiu a você', issue: 'FD-16', time: '2026-07-17T16:40:00', read: false },
  { id: 'n3', type: 'status', actor: 'u5', verb: 'concluiu', issue: 'FD-24', time: '2026-07-17T11:05:00', read: false },
  { id: 'n4', type: 'mention', actor: 'u3', verb: 'mencionou você em', issue: 'FD-12', time: '2026-07-16T15:22:00', read: true },
  { id: 'n5', type: 'status', actor: 'u9', verb: 'concluiu', issue: 'FD-3', time: '2026-07-15T10:02:00', read: true },
  { id: 'n6', type: 'assign', actor: 'u1', verb: 'atribuiu FD-15 a Otávio', issue: 'FD-15', time: '2026-07-14T09:30:00', read: true }
];

export const ACTIVITY = [
  { who: 'u2', what: 'mencionou você em', issue: 'FD-1', when: '2026-07-18T09:12:00' },
  { who: 'u5', what: 'concluiu', issue: 'FD-24', when: '2026-07-18T08:45:00' },
  { who: 'u6', what: 'comentou em', issue: 'FD-6', when: '2026-07-18T08:05:00' },
  { who: 'u4', what: 'moveu para Todo', issue: 'FD-11', when: '2026-07-17T11:55:00' },
  { who: 'u3', what: 'mencionou você em', issue: 'FD-12', when: '2026-07-16T15:22:00' },
  { who: 'u9', what: 'concluiu', issue: 'FD-3', when: '2026-07-15T10:02:00' }
];

export const INVITES = [
  { id: 'i1', email: 'ana.beltrao@estudiopau.com.br', role: 'Membro', sent: '2026-07-16T10:00:00' },
  { id: 'i2', email: 'joao.tavares@velalabs.com.br', role: 'Membro', sent: '2026-07-14T15:30:00' },
  { id: 'i3', email: 'consultoria@nortedados.com.br', role: 'Convidado', sent: '2026-07-08T09:15:00' }
];

const circ = { width: '14px', height: '14px', borderRadius: '50%', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', flex: 'none', boxSizing: 'border-box' };
const none = { display: 'none' };
export const STATUS = {
  backlog: { key: 'backlog', label: 'Backlog', order: 0, outer: { ...circ, border: '1.5px dashed var(--t3)' }, inner: none, glyph: '' },
  todo: { key: 'todo', label: 'Todo', order: 1, outer: { ...circ, border: '1.5px solid var(--t2)' }, inner: none, glyph: '' },
  in_progress: { key: 'in_progress', label: 'Em andamento', order: 2, outer: { ...circ, border: '1.5px solid var(--amber)' }, inner: { width: '7px', height: '7px', borderRadius: '50%', background: 'conic-gradient(var(--amber) 0 180deg, transparent 180deg 360deg)', display: 'block' }, glyph: '' },
  done: { key: 'done', label: 'Concluída', order: 3, outer: { ...circ, background: 'var(--green)' }, inner: { color: 'var(--bg)', fontSize: '9px', fontWeight: '800', lineHeight: '1' }, glyph: '✓' },
  canceled: { key: 'canceled', label: 'Cancelada', order: 4, outer: { ...circ, background: 'var(--t3)' }, inner: { color: 'var(--bg)', fontSize: '10px', fontWeight: '800', lineHeight: '1' }, glyph: '×' }
};
export const STATUS_LIST = ['backlog', 'todo', 'in_progress', 'done', 'canceled'];

const pbox = { width: '15px', height: '14px', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', flex: 'none' };
const bars = (a, b, c) => ({ width: '13px', height: '11px', flex: 'none', backgroundImage: `linear-gradient(${a},${a}),linear-gradient(${b},${b}),linear-gradient(${c},${c})`, backgroundSize: '3px 45%,3px 72%,3px 100%', backgroundPosition: '0 100%,5px 100%,10px 100%', backgroundRepeat: 'no-repeat' });
export const PRIORITY = {
  urgent: { key: 'urgent', label: 'Urgente', order: 0, outer: { ...pbox, background: 'var(--red)', borderRadius: '3.5px' }, inner: { color: '#FFFDF8', fontSize: '10.5px', fontWeight: '800', lineHeight: '1' }, glyph: '!' },
  high: { key: 'high', label: 'Alta', order: 1, outer: bars('var(--text)', 'var(--text)', 'var(--text)'), inner: none, glyph: '' },
  medium: { key: 'medium', label: 'Média', order: 2, outer: bars('var(--text)', 'var(--text)', 'var(--border2)'), inner: none, glyph: '' },
  low: { key: 'low', label: 'Baixa', order: 3, outer: bars('var(--text)', 'var(--border2)', 'var(--border2)'), inner: none, glyph: '' },
  none: { key: 'none', label: 'Sem prioridade', order: 4, outer: { ...pbox }, inner: { color: 'var(--t3)', fontSize: '11px', fontWeight: '700', lineHeight: '1' }, glyph: '—' }
};
export const PRIORITY_LIST = ['urgent', 'high', 'medium', 'low', 'none'];
export const ESTIMATES = [1, 2, 3, 5, 8];
export const SKELS = [1, 2, 3, 4, 5, 6, 7, 8];

export const uById = id => USERS.find(u => u.id === id) || null;
export const pById = id => PROJECTS.find(p => p.id === id) || null;
export const lById = id => LABELS.find(l => l.id === id) || null;

const MESES = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez'];
export function fmtDate(iso) { if (!iso) return '—'; const d = new Date(iso); return d.getDate() + ' ' + MESES[d.getMonth()]; }
export function timeAgo(iso) {
  const s = (Date.now() - new Date(iso).getTime()) / 1000;
  if (s < 60) return 'agora';
  if (s < 3600) return Math.floor(s / 60) + ' min';
  if (s < 86400) return Math.floor(s / 3600) + ' h';
  if (s < 86400 * 7) return Math.floor(s / 86400) + ' d';
  return fmtDate(iso);
}
export function saudacao() { const h = new Date().getHours(); return h < 12 ? 'Bom dia' : h < 18 ? 'Boa tarde' : 'Boa noite'; }
export function hojeLongo() { const s = new Date().toLocaleDateString('pt-BR', { weekday: 'long', day: 'numeric', month: 'long' }); return s.charAt(0).toUpperCase() + s.slice(1); }

export function hydrate(i) {
  const labs = (i.labels || []).map(lById).filter(Boolean);
  return {
    ...i,
    st: STATUS[i.status], pr: PRIORITY[i.priority],
    user: uById(i.assignee), proj: pById(i.project), labs,
    when: timeAgo(i.updated), dueTxt: i.due ? fmtDate(i.due) : '—',
    estTxt: i.estimate ? i.estimate + ' pts' : '—',
    descBlocks: i.desc || [{ t: 'p', x: i.d || 'Sem descrição por enquanto.' }]
  };
}
