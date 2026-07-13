# 10 — Padrões de Código

Este documento detalha, no nível de linha de código, o que `CLAUDE.md` estabelece estruturalmente. Em caso de dúvida sobre um caso não coberto aqui, o princípio de `CLAUDE.md` §1 ("clareza sobre esperteza") decide.

## 1. Padrões de nomenclatura

- **Backend (Python)**: módulos e funções `snake_case`; classes `PascalCase`; constantes `UPPER_SNAKE_CASE`; nomes de booleanos com prefixo `is_`/`has_`/`should_` (`is_active`, `has_permission`); nomes de função começam com verbo (`get_issue`, `create_workspace`, nunca `issue_get`).
- **Frontend (TypeScript)**: componentes e tipos/interfaces `PascalCase`; variáveis, funções e propriedades `camelCase`; hooks sempre prefixados `use` (`useIssueBoard`); booleanos com o mesmo prefixo semântico do backend (`isLoading`, `hasError`); handlers de evento prefixados `handle` (`handleStatusChange`) quando internos ao componente, `on` (`onStatusChange`) quando recebidos como prop.
- **Ambos**: nomes revelam intenção, não tipo ou implementação (`issues`, não `issueList` ou `issueArray`; `httpClient`, não `axiosInstanceWrapper`).

## 2. Organização de arquivos

- Um arquivo, uma responsabilidade principal (um componente, um service, um conjunto coeso de funções utilitárias relacionadas). Um arquivo que mistura duas responsabilidades não relacionadas deve ser dividido.
- Tamanho não é uma regra rígida, mas um arquivo de service ou componente que passa de ~300 linhas é sinal de que está absorvendo responsabilidade que deveria estar em outro lugar (um sub-hook, um service auxiliar) — revisar em code review, não dividir mecanicamente por contagem de linha.
- Testes ficam ao lado do código testado (`issue_service.py` + `test_issue_service.py` no mesmo diretório, backend) ou em `tests/` espelhando a estrutura de `src/` (frontend) — a convenção por linguagem segue o padrão idiomático de cada ecossistema, documentada aqui para não haver ambiguidade dentro do próprio projeto.

## 3. Convenções de import

- **Python**: ordem de import gerenciada automaticamente por Ruff (stdlib → third-party → first-party/local), sem import relativo além de um nível (`from .schemas import X`, nunca `from ...core.x import Y` — se a distância for grande, é sinal de acoplamento a revisar).
- **TypeScript**: imports absolutos a partir de `src/` via alias configurado no `tsconfig`/`vite.config` (`@/features/issues`, não `../../../features/issues`); import de biblioteca externa sempre antes de import interno, separados por linha em branco (aplicado automaticamente por ESLint + Prettier, não policiado manualmente).
- Nenhum import de conveniência do tipo `export * from` em barrels de feature grandes (`docs/05-frontend.md` §1) — exports nomeados explícitos, para que a árvore de dependência entre features permaneça rastreável por uma ferramenta estática.

## 4. Princípios de Clean Code aplicados

- Funções pequenas, um nível de abstração por função — uma função de service que orquestra 5 passos de negócio delega cada passo a uma função/método nomeado, não os inline em um bloco de 80 linhas.
- Nomes substituem comentários explicativos: se a única forma de tornar uma função clara é comentá-la, o nome (da função, das variáveis) provavelmente está errado — renomear primeiro, comentar apenas o que sobrar de não-óbvio (`CLAUDE.md` §17).
- Early return para reduzir aninhamento (`if not user: raise ...` no topo da função, em vez de todo o corpo dentro de um único `if user:`).
- Evitar flags booleanas de parâmetro que alteram o comportamento de uma função de forma não-óbvia pelo nome (`create_issue(data, skip_validation=True)` esconde um caminho de código relevante atrás de um argumento posicional fácil de não perceber em uma chamada) — preferir funções nomeadas separadamente quando o comportamento realmente diverge (`create_issue` vs. `import_issue` sem validação de origem externa).

## 5. Boas práticas de TypeScript

- `strict: true` no `tsconfig` sem exceção — `any` é proibido em código de aplicação (permitido, com justificativa em comentário, apenas ao tipar a borda de uma biblioteca de terceiro sem tipos).
- Tipos de domínio (`Issue`, `Workspace`) são a fonte de verdade de forma — derivados manualmente do schema Pydantic do backend hoje (ADR-001 nota a ausência de geração automática); campos opcionais representados com `?`, nunca com `| null` misturado a `?` no mesmo campo sem necessidade semântica real de distinguir "ausente" de "nulo".
- Preferir `type` para uniões/interseções e `interface` para formas de objeto extensíveis (props de componente, DTOs) — escolha consistente, não alternância arbitrária dentro do mesmo arquivo.
- Nunca usar `as` para forçar um tipo que o compilador rejeitou sem uma verificação em runtime que justifique a garantia (type assertion é uma promessa ao compilador; quebrá-la sem uma checagem real é o bug mais comum de "TypeScript não tipado de verdade").
- `unknown` em vez de `any` para dado de fronteira (resposta de rede antes de validação) — validado por Zod antes de ser tratado como o tipo esperado.

## 6. Boas práticas de Python

- Type hints obrigatórios em toda função pública (parâmetros e retorno) — checado por Mypy em modo estrito no CI; `Any` evitado pelas mesmas razões que `any` em TS.
- `Protocol` (não classe abstrata `ABC`) para interfaces de repository — permite que um fake de teste satisfaça o contrato por estrutura, sem herdar de uma classe base artificial.
- Dataclasses (`@dataclass` ou Pydantic, conforme o caso) em vez de dicionários soltos (`dict[str, Any]`) para qualquer estrutura de dado que atravesse mais de uma função — um dicionário solto não documenta sua própria forma.
- `async`/`await` consistente em toda a cadeia de I/O (nunca misturar chamada síncrona bloqueante — ex.: uma biblioteca HTTP síncrona — dentro de um handler async sem rodar em thread pool explícito).
- Nenhuma lógica de negócio em `__init__.py` — arquivos de inicialização de pacote existem apenas para definir o que é exportado publicamente.

## 7. Comentários

- Regra única: comentário explica **por quê**, nunca **o quê** (`CLAUDE.md` §17). Um comentário que poderia ser deletado sem confundir um leitor futuro deveria ser deletado.
- Comentários `TODO`/`FIXME` sempre acompanhados de contexto mínimo (por que não foi resolvido agora) — nunca um `TODO` solto sem explicação, que se torna ruído permanente.
- Código comentado ("deixa aí comentado por precaução") nunca é commitado — o histórico do git já preserva a versão anterior; código morto comentado é confundido com intenção ativa por quem lê depois.

## 8. Documentação

- Documentação de arquitetura/produto vive em `docs/`, não em comentário de código nem em wiki externa — mantém uma única fonte de verdade versionada junto ao código que ela descreve.
- Mudança de contrato de API, schema de banco ou decisão arquitetural relevante é documentada no mesmo PR que a implementa (`CLAUDE.md` §17) — documentação retroativa ("depois eu atualizo os docs") não é aceita como prática do projeto.
- Docstring de função pública de service, quando existe, descreve a regra de negócio não-óbvia que a função encapsula (ex.: por que uma transição de status é validada contra o workflow do time) — não uma paráfrase da assinatura.

## 9. Tratamento de erros

- Backend: exceções de domínio (`CLAUDE.md` §7) — nunca capturar `Exception` genericamente para engolir erro; nunca retornar `None`/`False` silenciosamente onde uma exceção é a resposta correta (um `get_by_id` que não encontra o recurso lança `NotFoundError`, não retorna `None` para o chamador decidir — centraliza a decisão de "o que significa ausência" em um único lugar).
- Frontend: erros de mutation/query do TanStack Query são tratados no nível da feature (mensagem de erro amigável baseada no `code` do envelope de erro, `CLAUDE.md` §8) — nunca um `try/catch` vazio ou um `.catch(() => {})` que descarta o erro sem feedback ao usuário nem log.
- Erros inesperados (não mapeados para um `code` conhecido) sempre resultam em um estado de UI genérico ("algo deu errado, tente novamente") mais um log via `console.error`/serviço de erro — nunca uma tela em branco silenciosa.

## 10. Padrões de testes

- Nomenclatura de teste descreve comportamento, não implementação: `test_update_status_raises_conflict_when_transition_invalid`, não `test_update_status_2`.
- Estrutura Arrange-Act-Assert (ou Given-When-Then) explícita, com as três seções visualmente separadas mesmo sem comentário rotulando-as.
- Teste unitário de service não tem I/O real (repository é fake/in-memory); teste de integração de repository usa banco de teste real (não mock de SQLAlchemy) — mockar o próprio ORM testaria o mock, não o comportamento real de query.
- Um teste, uma asserção de comportamento (múltiplas chamadas `assert` são aceitáveis se todas verificam facetas do mesmo comportamento sendo testado; um único arquivo de teste testando duas regras de negócio não relacionadas deve ser dividido).
- Dado de teste construído via factories/builders nomeados (`make_issue(status="done")`), nunca fixtures gigantes compartilhadas entre testes não relacionados que tornam uma falha difícil de rastrear à causa raiz.
