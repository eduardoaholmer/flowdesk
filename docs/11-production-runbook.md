# 11 — Runbook de Produção (Sprint 17.5/M6, ADR-041)

> Este documento fecha o M6 — Production. Não é um plano de implementação: é a
> decisão registrada, para cada item de `PRODUCTION_CHECKLIST.md` marcado como
> "requer infraestrutura externa", de **qual seria a estratégia real** se este
> projeto algum dia ganhasse um ambiente de produção de fato. Nenhum item aqui
> vira código — decisão explícita do usuário (ADR-036): construir infraestrutura
> "de mentira" (MinIO simulando produção, TLS self-signed) só para preencher
> este checklist seria o mesmo problema que generalidade especulativa
> (`CLAUDE.md` §1.6) — complexidade nova sem consumidor real. Se um ambiente de
> produção real vier a existir, este runbook é o ponto de partida, não um
> substituto para julgamento operacional no momento.

## 1. Segredos reais em um gerenciador de segredos

**Estratégia recomendada**: GitHub Environments (secrets por ambiente, já que o
CI já vive em GitHub Actions — zero conta nova) para segredos injetados no
deploy; um secret manager dedicado (AWS Secrets Manager, HashiCorp Vault) só
se o ambiente de deploy real não for GitHub-nativo. Gerar o par JWT via
`openssl genrsa`/`openssl rsa` (mesmo comando já documentado em `.env.example`),
armazenar no gerenciador escolhido, nunca no repositório.

**Já pronto no código**: `Settings` falha na inicialização se `ENVIRONMENT=production`
usar o par de chave JWT de desenvolvimento (ADR-008) ou se faltar qualquer
variável obrigatória; `.env.production.example` (Sprint 17.4/M6, ADR-040) já
documenta o conjunto completo esperado.

## 2. Pipeline de deploy real

**Estratégia recomendada**: estender `.github/workflows/ci.yml` com um job
`deploy`, condicionado a `push` em `main` e ao job `docker` ter passado — build
+ tag da imagem pelo SHA do commit, push para o GitHub Container Registry
(GHCR, natural por já estarmos em GitHub — zero conta nova), depois disparar o
deploy no orquestrador real (`kubectl set image`, `docker service update`, ou
o webhook de um PaaS como Render/Fly.io/Railway, dependendo de onde a
aplicação realmente rodasse).

**Já pronto no código**: o job `docker` já builda e valida as duas imagens de
produção em todo PR (`push: false` até aqui); os Dockerfiles já são
imutáveis-por-tag, non-root, sem dependência de dev.

**Não escolhido deliberadamente**: nenhum orquestrador específico é
provisionado aqui — não existe cluster, conta de PaaS ou ambiente de produção
real para este projeto de portfólio.

## 3. Migração de banco como etapa explícita do deploy

**Estratégia recomendada**: o job `deploy` (item 2) roda `alembic upgrade head`
contra o banco real como etapa obrigatória **antes** de trocar o tráfego para
a imagem nova — mesmo step "Alembic upgrade head" que o CI já roda hoje, só
que contra o DSN real em vez do Postgres efêmero do CI.

**Risco a observar**: para um deploy de fato zero-downtime, toda migration
precisa ser compatível com a versão anterior ainda em execução (padrão
expand → backfill → contract) — já é a norma neste projeto (`docs/03-database.md`
documenta explicitamente por que `NOT NULL` direto com `server_default` foi
aceitável em várias migrations passadas: a tabela nunca tinha linha em
produção ainda. Esse atalho deixa de ser válido no dia em que houver dado real
em produção — a migration seguinte precisaria voltar ao padrão expand/contract
completo).

## 4. Agregação/retenção de log centralizada

**Estratégia recomendada**: encaminhar as linhas JSON do `structlog` via o
driver de log nativo da plataforma de deploy (CloudWatch Logs se em
AWS/ECS, ou Loki via um sidecar `promtail`/`vector` em self-hosting) — zero
mudança de código, o formato JSON estruturado já é o pré-requisito.

**Já pronto no código**: `AccessLogMiddleware` + logging estruturado em JSON
desde a Sprint 8.7, `request_id` de correlação ponta a ponta.

## 5. Métricas de série temporal (Prometheus/OpenTelemetry)

Permanece deliberadamente fora de escopo (decisão já registrada na ADR-016) —
`GET /metrics` (Sprint 14.5, agregação via Redis) cobre "métricas básicas via
log agregável" o suficiente para o estágio atual do projeto. Só reconsiderar
se um ambiente real de produção pedir dashboards Grafana/alertas automáticos.

## 6. Backup automatizado do Postgres

**Estratégia recomendada**: preferir o backup nativo de um provedor de
Postgres gerenciado (RDS, Cloud SQL, Neon — a maioria oferece backup diário +
point-in-time recovery nativamente, estritamente melhor que um cron de
`pg_dump` administrado à mão) sobre uma solução artesanal. Se um Postgres
autogerenciado for mesmo necessário: `pg_dump` agendado + retenção de N dias
**+ teste periódico de restore** — um backup nunca restaurado não é um backup
confiável, é só uma suposição.

Este é o item mais importante de todo o runbook para acertar de fato num
deploy real — perda de dado é o modo de falha menos reversível de tudo que
este documento cobre.

**Já pronto no código**: nada depende de mudança de código — é 100% decisão de
infraestrutura/operação.

## 7. Backup dos anexos enviados

**Estratégia recomendada**: com `STORAGE_PROVIDER=s3` configurado (Sprint
17.2/M6, ADR-038), versionamento de bucket + replicação entre regiões (ambos
recursos nativos de S3/R2/Spaces, zero código de aplicação) resolvem isso.
`LocalStorageProvider` (disco local) não tem — nem deveria ter — uma história
de backup própria: é o default de instância única para dev/demo, não o modo
de produção real.

**Já pronto no código**: `S3StorageProvider` é o pré-requisito que desbloqueia
este item — entregue.

## 8. Runbook de rollback testado

**Estratégia recomendada**: (a) confirmar que a tag/SHA da imagem anterior
ainda está disponível no registry; (b) reapontar o orquestrador/compose para
essa tag; (c) se o deploy que falhou incluiu uma migration, rodar
`alembic downgrade -1` **antes** de reverter a imagem da aplicação, nunca
depois — uma versão antiga do app consultando um schema mais novo é
exatamente o perigo que as migrations reversíveis deste projeto já foram
desenhadas para evitar. Deveria ser ensaiado ao menos uma vez contra um
ambiente de staging antes de ser confiado num incidente real.

**Já pronto no código**: imagens imutáveis por tag (Sprint 8.7); toda migration
já registrada neste projeto é reversível via `alembic downgrade` (nenhuma
migration destrutiva sem um trade-off explícito em ADR até hoje).

## 9. Certificado TLS e terminador HTTPS na borda

**Estratégia recomendada**: terminar TLS na borda — um load balancer gerenciado
(ALB, Cloud Load Balancing) ou um proxy reverso com provisionamento automático
de certificado (Caddy, ou Nginx + certbot) na frente dos containers
`frontend`/`backend`. A aplicação em si nunca termina TLS.

**Já pronto no código**: `Strict-Transport-Security` já condicionado a
`ENVIRONMENT=production` (Sprint 8.7, `docs/07-security.md` §14) — pronto no
instante em que um terminador TLS real existir na frente.

## 10. Autoscaling horizontal real

**Estratégia recomendada**: autoscaling nativo do orquestrador escolhido (HPA
do Kubernetes, Service Auto Scaling do ECS, o scale-to-N nativo de um PaaS) — o
app já satisfaz o pré-requisito (backend stateless, sessão em Postgres/Redis
não em memória do processo, clientes de banco/Redis com `pool_pre_ping`/
reconexão automática). O único bloqueio remanescente antes de rodar múltiplas
instâncias de fato era o armazenamento de anexos (item 7) — resolvido desde a
Sprint 17.2.

**Já pronto no código**: `--workers 4` fixo por imagem é o teto de
escala-vertical por instância; elasticidade real é escala-horizontal (mais
instâncias), o que a recomendação acima endereça.
