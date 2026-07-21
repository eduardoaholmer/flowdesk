# Checklist de Prontidão para Produção

Este checklist reflete o estado real do repositório após a Sprint 8.7 (`docs/08-roadmap.md`,
ADR-016 em `docs/09-decision-log.md`). Ele é deliberadamente honesto sobre o que está
implementado **no código deste repositório** versus o que depende de infraestrutura real que um
projeto de portfólio não provisiona (um banco gerenciado, um serviço de backup, um provedor de
TLS). Itens do segundo tipo estão marcados como "requer infraestrutura externa".

## Ambiente

- [x] Configuração via variável de ambiente, nunca hardcoded (`backend/src/core/config.py`).
- [x] Falha rápida na inicialização se uma variável obrigatória estiver ausente ou tiver um valor
      inválido (`DATABASE_URL`/`JWT_PRIVATE_KEY`/`REDIS_URL` ausentes, `ENVIRONMENT` fora do
      conjunto `development`/`test`/`production`).
- [x] Trava de segurança: recusa subir com `ENVIRONMENT=production` usando a chave JWT de
      desenvolvimento checada no repositório.
- [x] Referência completa de variáveis de ambiente: `docs/06-backend.md` §10.
- [x] Template `.env.production.example` (raiz, Sprint 17.4/M6, ADR-040) documentando o conjunto
      completo de variáveis esperado especificamente em produção — placeholders (`CHANGE_ME`),
      nunca valores reais utilizáveis.
- [ ] Segredos reais (chave JWT de produção, credenciais de banco) gerados e armazenados em um
      gerenciador de segredos — **requer infraestrutura externa** (Vault, AWS Secrets Manager,
      GitHub Environments, etc.). Nunca em `.env` commitado.

## Deploy

- [x] Imagens Docker de produção (`docker/backend.Dockerfile`/`docker/frontend.Dockerfile`,
      target `production`): sem hot-reload, sem dependências de dev, sem bind mount de
      código-fonte, containers non-root.
- [x] `docker-compose.prod.yml` demonstrando a topologia completa (Postgres, Redis, backend,
      frontend atrás de Nginx).
- [x] CI builda as duas imagens de produção em todo PR (`.github/workflows/ci.yml`, job `docker`)
      — quebra de Dockerfile é pega antes do merge.
- [ ] Pipeline de deploy real (build → push para registry → deploy em orquestrador) —
      **requer infraestrutura externa**. O que existe aqui é a base (imagens corretas, CI que as
      valida), não o pipeline em si.
- [ ] Migração de banco (`alembic upgrade head`) como etapa explícita e obrigatória do deploy,
      antes de trocar o tráfego para a nova versão — hoje só roda em CI, contra um banco efêmero.

## Monitoramento e Observabilidade

- [x] Logging estruturado em JSON em produção (`structlog`), com `timestamp`/`level`/
      `request_id`/`user_id`/`environment` em toda linha.
- [x] `request_id` de correlação ponta a ponta (`X-Request-ID`), aceito do cliente quando é um
      UUID válido, gerado caso contrário.
- [x] Linha de access-log estruturada por requisição (`http_request`: método, path, status,
      duração).
- [x] `GET /health` (liveness) e `GET /health/ready` (readiness — banco/Redis/storage,
      extensível para novos serviços via `core/health.py`).
- [x] `GET /version` com versão, ambiente e `uptime_seconds`.
- [ ] Agregação/retenção de log centralizada (ELK, Loki, CloudWatch Logs) — **requer
      infraestrutura externa**. O formato JSON estruturado já é o pré-requisito para conectar a
      qualquer uma dessas ferramentas sem mudança de código.
- [ ] Métricas de série temporal (Prometheus/OpenTelemetry) e alerta automático — deliberadamente
      fora de escopo desta sprint (ADR-016); a linha de access-log já cobre "métricas básicas via
      log agregável" o suficiente para o estágio atual do projeto.

## Backups

- [ ] Backup automatizado do Postgres — **requer infraestrutura externa** (a maioria dos
      provedores gerenciados de Postgres oferece isso nativamente). Estratégia recomendada para
      quando houver um banco real: `pg_dump` agendado + retenção de N dias + teste periódico de
      restore (um backup nunca testado não é um backup confiável).
- [ ] Backup dos anexos enviados (`var/uploads` local, `core/storage.py::LocalStorageProvider`) —
      hoje é armazenamento em disco local de instância única, sem replicação; migrar para um
      provider de objeto remoto (S3 ou equivalente, o `StorageProvider` já é o ponto de extensão
      para isso) é pré-requisito para backup real de anexos.

## Rollback

- [x] Imagens Docker imutáveis por tag/build — reverter é trocar a imagem em execução, não
      reconstruir.
- [x] Migrations Alembic são incrementais e cada uma é reversível via `alembic downgrade` (padrão
      já seguido desde a Sprint 2, não introduzido nesta sprint).
- [ ] Runbook de rollback testado (não só teoricamente possível) contra um ambiente real —
      **requer infraestrutura externa** para validar de ponta a ponta.

## Segurança

- [x] Cookies de autenticação `HttpOnly`/`Secure`/`SameSite=Strict`; CSRF double-submit em
      `/auth/refresh` (`docs/07-security.md` §3-4).
- [x] Rate limiting via Redis (janela deslizante), diferenciado por sensibilidade de rota.
- [x] Security headers em toda resposta (`X-Content-Type-Options`, `X-Frame-Options`,
      `Referrer-Policy`, `Permissions-Policy`, HSTS em produção — `docs/07-security.md` §14).
- [x] CORS com origem/métodos/headers explícitos, nunca wildcard combinado com credenciais.
- [x] `pip-audit`/`npm audit` em CI (não bloqueantes) + Dependabot semanal para as três
      ecosystems do projeto.
- [x] Hash de senha Argon2id; JWT RS256 de vida curta + refresh token rotativo com detecção de
      reuso (`docs/07-security.md` §1-2).
- [ ] Certificado TLS e terminador HTTPS na borda — **requer infraestrutura externa** (load
      balancer gerenciado, Caddy/Nginx com Let's Encrypt, ou equivalente). O `Strict-Transport-
      Security` já está condicionado a `ENVIRONMENT=production`, pronto para quando isso existir.
- [x] Varredura de vulnerabilidade de imagem Docker via Trivy (Sprint 17.4/M6, ADR-040) — job
      `docker` do CI, não bloqueante (mesmo critério de `pip-audit`/`npm audit`), `CRITICAL`/`HIGH`.

## Escalabilidade

- [x] Backend stateless (sessão vive em Postgres/Redis, não em memória do processo) — múltiplas
      réplicas atrás de um load balancer funcionam sem sticky session.
- [x] Imagem de produção do backend já roda com múltiplos workers Uvicorn (`--workers 4`, fixo
      por imagem — CLAUDE.md §1.6, ajustar exige nova imagem, não uma env var lida em runtime).
- [x] Engine de banco e cliente Redis com `pool_pre_ping`/reconexão automática por event loop.
- [ ] Autoscaling horizontal real (múltiplas instâncias, load balancer) — **requer
      infraestrutura externa** de orquestração (o app já é stateless o suficiente para isso hoje).
- [x] Armazenamento de anexos com provider remoto disponível (`S3StorageProvider`, Sprint 17.2/M6,
      ADR-038) — `STORAGE_PROVIDER=s3` + `S3_BUCKET_NAME` troca `LocalStorageProvider` (disco
      local, não compartilhado entre réplicas) por um bucket S3-compatible sem mudar o contrato
      de `AttachmentService`. Default do app continua `local`; rodar múltiplas instâncias de fato
      exige configurar `s3` explicitamente — nenhum bucket real é provisionado por este repositório.
