# Deploy — FlowDesk em produção

Domínio final: `flowdesk.eduardoaholmer.dev` (subdomínio de `eduardoaholmer.dev`,
registrado na Namecheap).

| Camada | Serviço | Config no repo |
|---|---|---|
| Backend | Render (Docker, Blueprint) | `render.yaml` (raiz) + `backend/render_start.sh` |
| Postgres | Supabase | env `DATABASE_URL` no Render |
| Redis | Upstash | env `REDIS_URL` no Render |
| Frontend | Vercel | `frontend/vercel.json` + `frontend/.env.example` |
| DNS | Namecheap (Advanced DNS) | CNAME `flowdesk` → Vercel |

Este arquivo documenta a Parte 1 (repositório) e será atualizado com os valores
reais depois da Parte 2 (provisionamento nos painéis). **Segredos nunca vão
para este arquivo nem para o repositório** — só nos painéis do Render/Vercel.

## Parte 1 — Repositório (feito)

- **Start command com migration automática**: `backend/render_start.sh` roda
  `alembic upgrade head` antes de subir o Uvicorn. É o `dockerCommand` usado
  pelo `render.yaml`.
- **Health check**: `GET /health` (liveness, sem I/O) e `GET /health/ready`
  (readiness — checa Postgres/Redis). `render.yaml` aponta
  `healthCheckPath: /health/ready`.
- **CORS**: `backend/src/main.py` aceita a origem exata de `CORS_ORIGINS`
  (configurada no Render como `https://flowdesk.eduardoaholmer.dev`) mais
  qualquer preview da Vercel via `allow_origin_regex`
  (`^https://[a-zA-Z0-9-]+\.vercel\.app$`) — previews geram um subdomínio novo
  por PR e não cabem numa lista fixa.
- **`render.yaml`** (raiz, não em `backend/`): é um Blueprint — já provisiona
  Postgres (`flowdesk-postgres`) e Redis (`flowdesk-redis`) do próprio Render
  junto com o Web Service, então **não é usado neste deploy** (Supabase/Upstash
  substituem o Postgres/Redis do Render por escolha do usuário) — serve de
  referência para as env vars esperadas pelo backend. As env vars reais deste
  deploy são preenchidas manualmente no dashboard do Render ao criar o Web
  Service (ver Parte 2), apontando `DATABASE_URL`/`REDIS_URL` para
  Supabase/Upstash em vez de `fromDatabase`/`fromService`.
- **`.env.example`** (`backend/.env.example`, `.env.production.example` na
  raiz): já listam todas as variáveis esperadas (`DATABASE_URL`, `REDIS_URL`,
  `CORS_ORIGINS`, `JWT_PRIVATE_KEY`/`JWT_PUBLIC_KEY`, `FRONTEND_BASE_URL`,
  storage/mail opcionais) — nenhuma alteração necessária.
- **`frontend/.env.example`**: já tem `VITE_API_URL` apontando pro backend.

## Parte 2 — Provisionamento (concluído em 2026-09-08)

O Render já tinha um Web Service (`flowdesk-backend`) e um Postgres/Redis
próprios do Render deployados via `render.yaml` em sessão anterior — o
Postgres free do Render havia expirado (`Suspended by Render`, limite de 30
dias no free tier), o que deixava o backend em produção incapaz de conectar
ao banco. A Parte 2 migrou `DATABASE_URL`/`REDIS_URL` para Supabase/Upstash
(que não expiram) em vez de criar serviços do zero.

1. **Supabase** — projeto `flowdesk` criado (região West US/Oregon, Data API
   desabilitada — o backend fala com o Postgres direto via SQLAlchemy/asyncpg,
   não via REST do Supabase). Connection string usada é a do **Session
   Pooler** (IPv4), não a "Direct connection" (IPv6-only por padrão — o
   Render não tem egress IPv6, então Direct connection quebraria).
2. **Upstash** — instância Redis `flowdesk` free criada. Região ficou em São
   Paulo (`sa-east-1`) mesmo tendo selecionado Oregon manualmente — o plano
   free do Upstash parece ignorar a região primária escolhida.
3. **Render** — env vars do `flowdesk-backend` atualizadas (não foi criado um
   novo Web Service): `DATABASE_URL` → Supabase (session pooler),
   `REDIS_URL` → Upstash, `CORS_ORIGINS` →
   `https://flowdesk.eduardoaholmer.dev,https://flowdesk-ruby-beta.vercel.app`,
   `FRONTEND_BASE_URL` → `https://flowdesk.eduardoaholmer.dev`. Deploy
   disparado via "Save, rebuild, and deploy"; `alembic upgrade head` rodou
   todas as migrations do zero no banco novo com sucesso.
4. **Vercel** — projeto `flowdesk` já existia (deployado em sessão anterior,
   `flowdesk-ruby-beta.vercel.app`), conectado ao mesmo repo/branch `main`,
   com `VITE_API_URL` já apontando para o backend do Render.
5. **Vercel → Settings → Domains** — adicionado `flowdesk.eduardoaholmer.dev`
   (Production). CNAME exibido: Host `flowdesk` → Value
   `d992bf47352c080b.vercel-dns-017.com.`
6. **Namecheap → Advanced DNS** — CNAME `flowdesk` → o valor acima, adicionado
   sem alterar os registros existentes (`www`, `@`). Propagou em minutos;
   Vercel emitiu o certificado SSL automaticamente.
7. **Bug encontrado e corrigido**: o primeiro teste de login no domínio final
   deu `503`/preflight `400 Bad Request` — `CORS_ORIGINS` só tinha o domínio
   antigo da Vercel, então o navegador rejeitava o preflight OPTIONS antes de
   qualquer resposta do app (`Disallowed CORS origin`, comportamento padrão do
   `CORSMiddleware` do Starlette quando a origem não bate). Corrigido no passo
   3 acima; confirmado com `/auth/refresh` voltando `401` normalmente (não
   mais erro de CORS) no domínio final.

## Valores reais

| Variável | Valor |
|---|---|
| URL pública do backend (Render) | `https://flowdesk-backend-ngcl.onrender.com` |
| Connection string Postgres (Supabase) | só no painel do Render — não registrada aqui (session pooler, `aws-0-us-west-2.pooler.supabase.com:5432`) |
| URL Redis (Upstash) | só no painel do Render — não registrada aqui (`guided-grizzly-87434.upstash.io:6379`, TLS) |
| `VITE_API_URL` (Vercel) | `https://flowdesk-backend-ngcl.onrender.com/api/v1` |
| Domínio final | `https://flowdesk.eduardoaholmer.dev` — ativo, SSL válido |
| CNAME (Vercel → Namecheap) | Host `flowdesk` → `d992bf47352c080b.vercel-dns-017.com.` |

## Limpeza pós-migração (feita em 2026-09-08)

- `flowdesk-postgres` e `flowdesk-redis` (recursos nativos do Render, criados
  pelo Blueprint antigo) foram **deletados** no dashboard do Render — não são
  mais usados desde a migração para Supabase/Upstash acima.
- O Blueprint `flowdesk` (Render → Blueprints) tinha **Auto Sync: Yes**, o que
  faria o Render re-sincronizar `render.yaml` a cada push e **recriar**
  `flowdesk-postgres`/`flowdesk-redis` (o arquivo ainda os declara como
  referência — ver nota na Parte 1). Auto Sync foi trocado para **No**
  (`Sync paused`): `render.yaml` continua só como referência de env vars
  esperadas, sem provisionar nada automaticamente. Reativar Auto Sync sem
  antes remover `databases:`/o serviço `flowdesk-redis` do `render.yaml`
  voltaria a recriar os dois e resetaria `DATABASE_URL`/`REDIS_URL` para
  `fromDatabase`/`fromService` (quebrando a integração com Supabase/Upstash).

## Follow-up sugerido

- Backend no Render free tier "dorme" após ~15 min de inatividade (delay de
  até 50s na primeira requisição depois disso) — considerar upgrade de plano
  se isso for um problema para demonstrações ao vivo.
