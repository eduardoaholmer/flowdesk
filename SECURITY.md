# Política de Segurança

## Versões suportadas

FlowDesk é um projeto de portfólio em desenvolvimento ativo, sem releases versionados ainda.
Apenas o branch `main` recebe correções de segurança.

## Reportando uma vulnerabilidade

Se você encontrar uma vulnerabilidade de segurança neste projeto — especialmente qualquer coisa
relacionada a isolamento multi-tenant, autenticação, autorização (RBAC) ou exposição de dados
entre workspaces — por favor **não abra uma issue pública**.

Reporte de forma privada para **eduardoaholmer@gmail.com**, incluindo:

- Descrição da vulnerabilidade e impacto potencial.
- Passos para reproduzir (endpoint, payload, condições necessárias).
- Versão/commit afetado, se souber.

Você pode esperar uma resposta inicial em até 5 dias úteis. Como este é um projeto de portfólio
mantido por uma única pessoa, não há SLA formal, mas relatos válidos serão priorizados sobre
qualquer outro trabalho em andamento.

## Escopo

Este projeto segue os princípios de segurança descritos em
[`docs/07-security.md`](./docs/07-security.md) — isolamento de workspace, RBAC, e o fluxo de
autenticação via JWT + refresh token rotativo descritos em [`CLAUDE.md`](./CLAUDE.md) §11.
