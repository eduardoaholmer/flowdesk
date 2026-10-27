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
  (configurada no Render como `https://flowdesk.eduardoaholmer.dev`) e,
  opcionalmente, `CORS_ORIGIN_REGEX`. A regex fixa `*.vercel.app` foi removida
  (ADR-067): confiava em qualquer site de qualquer conta da Vercel. Com o
  proxy same-origin abaixo, nem produção nem previews precisam de CORS.
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
| `VITE_API_URL` (Vercel) | `/api/v1` — relativo, via proxy da Vercel (ADR-063). Antes: `https://flowdesk-backend-ngcl.onrender.com/api/v1` |
| Domínio final | `https://flowdesk.eduardoaholmer.dev` — ativo, SSL válido |
| CNAME (Vercel → Namecheap) | Host `flowdesk` → `d992bf47352c080b.vercel-dns-017.com.` |

## API same-origin via proxy da Vercel + login social (ADR-063)

O SPA não chama mais `onrender.com` direto: `frontend/vercel.json` reescreve
`/api/*` para `https://flowdesk-backend-ngcl.onrender.com/api/*`. Sem isso, o
cookie `csrf_token` ficava no domínio da API (ilegível pelo SPA) e o
`/auth/refresh` falhava sempre — quebrando o login com Google/GitHub e
derrubando a sessão a cada reload. Passos manuais para ativar:

1. **Vercel → Settings → Environment Variables**: `VITE_API_URL` = `/api/v1`
   (Production e Preview) e redeploy (variável `VITE_*` entra no build).
2. **Render → `flowdesk-backend` → Environment**:
   - `GOOGLE_REDIRECT_URI` = `https://flowdesk.eduardoaholmer.dev/api/v1/auth/google/callback`
   - `GITHUB_REDIRECT_URI` = `https://flowdesk.eduardoaholmer.dev/api/v1/auth/github/callback`
   - `GOOGLE_CLIENT_ID`/`GOOGLE_CLIENT_SECRET`/`GITHUB_CLIENT_ID`/`GITHUB_CLIENT_SECRET`
     preenchidos (sem eles o botão cai em `oauth_provider_not_configured`).
   - Salvar com "Save, rebuild, and deploy" (mudança de env var não entra no
     serviço em execução sem um novo deploy).
3. **Google Cloud Console → APIs & Services → Credentials → OAuth client**:
   em "Authorized redirect URIs", adicionar a URL de callback do Google acima
   (precisa bater exatamente, senão o Google responde `redirect_uri_mismatch`).
4. **GitHub → Settings → Developer settings → OAuth Apps → FlowDesk**:
   "Authorization callback URL" = a URL de callback do GitHub acima (o host
   precisa ser o mesmo do `redirect_uri` enviado, senão o GitHub recusa).

Feito e validado em produção em 2026-10-26 (login com Google e GitHub
concluindo na home, sessão mantida após reload). Ordem recomendada: 2 → 3 → 4 → 1. `CORS_ORIGINS` não precisa mudar (com o
proxy as chamadas do SPA são same-origin e nem passam por CORS).

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

## Como redeployar (atualizado em 2026-10-26)

- **Vercel (frontend):** auto-deploy já ativo — todo push em `main` dispara
  build/deploy sozinho, sem passo manual.
- **Render (backend): auto-deploy LIGADO (`On Commit`).** Visto no dashboard
  em 2026-10-26 (`flowdesk-backend` → Settings → Deploy → Auto-Deploy). Até
  2026-10-22 os deploys eram todos `Trigger: Manual`; não há registro de quem
  ligou nem quando. Hoje todo push em `main` redeploya o backend, rodando
  `alembic upgrade head` (`backend/render_start.sh`).
  - Deploy manual continua disponível: `flowdesk-backend` → **Manual Deploy**
    → **Deploy latest commit**.
  - Para voltar ao controle manual: Settings → Deploy → Auto-Deploy → `Off`.

## Pendências de CORS e rede (ADR-067)

- **CORS**: a regex fixa `*.vercel.app` saiu do backend (confiava, com
  credenciais, em qualquer site de qualquer conta da Vercel). Com
  `VITE_API_URL=/api/v1` também em Preview, cada preview usa o próprio proxy
  e nenhuma `CORS_ORIGIN_REGEX` é necessária.
- **Follow-up**: com o proxy validado (ADR-063), os cookies de auth podem
  voltar a `SameSite=Strict` em produção (hoje `None`, ADR-062), e
  `CORS_ORIGINS` no Render pode ficar só com o domínio final.
- **Rate limit por IP (não resolvido)**: o Uvicorn roda sem
  `--forwarded-allow-ips`, então `request.client.host` é o IP do proxy (Render,
  e agora também Vercel), não o do usuário — o limite de 5 logins/min por IP
  vira, na prática, um limite global compartilhado. Corrigir exige confirmar em
  produção qual cabeçalho/posição de `X-Forwarded-For` carrega o IP real depois
  dos dois proxies; confiar cegamente em `X-Forwarded-For` deixaria o cliente
  forjar o próprio IP e furar o limite.

## Keep-alive do backend (UptimeRobot, configurado em 2026-10-26)

O Render free tier "dorme" o serviço após ~15 min sem requisições, e a
primeira requisição seguinte espera ~1 min pelo cold start. No login social
isso aparecia como a página de carregamento do Render antes do redirect para
o Google/GitHub.

- **Monitor**: UptimeRobot (plano free), tipo HTTP(s), intervalo de 5 min,
  alerta por e-mail para o dono da conta.
- **URL**: `https://flowdesk-backend-ngcl.onrender.com/health/ready`. Usa
  `/health/ready` (não `/health`) para que o ping também toque Postgres
  (Supabase) e Redis (Upstash): o Supabase free pausa o projeto após 7 dias
  sem atividade. Custo: ~9 mil requisições/mês, dentro dos limites free.
- **Horas do Render**: um serviço acordado 24/7 consome ~744 h/mês, dentro das
  750 h/mês do free tier — não sobra margem para um segundo serviço free
  acordado o tempo todo.
- Alternativa sem keep-alive: plano pago do Render (Starter), que não dorme.
