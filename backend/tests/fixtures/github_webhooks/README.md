# Payloads de webhook do GitHub

Exemplos reais de corpo de entrega, copiados sem alteração de
[`octokit/webhooks`](https://github.com/octokit/webhooks) (`payload-examples/api.github.com/`,
licença MIT, Copyright (c) 2018 Gregor Martynus). Usados pelos testes do webhook
(`tests/contract/test_github_webhook.py`), que trocam só o `installation.id` pelo de uma
instalação conectada no teste e assinam o corpo com o segredo de teste.

| Arquivo | Origem |
|---|---|
| `installation_created.json` | `installation/created.payload.json` |
| `installation_deleted.json` | `installation/deleted.payload.json` |
| `installation_suspend.json` | `installation/suspend.payload.json` |
| `installation_unsuspend.json` | `installation/unsuspend.payload.json` |
| `installation_repositories_added.json` | `installation_repositories/added.payload.json` |
| `pull_request_opened.json` | `pull_request/opened.payload.json` |
| `ping.json` | `ping/payload.json` |
