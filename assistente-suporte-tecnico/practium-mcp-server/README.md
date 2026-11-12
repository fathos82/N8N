# practium-support-mcp-sim (T-007)

Servidor **MCP real** (Model Context Protocol) que simula o diagnóstico ativo da Flora para o
Practium. Ele usa o SDK oficial `@modelcontextprotocol/sdk` e transporte **Streamable HTTP**,
o mesmo aceito pelo nó `MCP Client Tool` do n8n instalado (n8n 2.102.0, `serverTransport:
httpStreamable`; SSE existe como opção depreciada).

> **Aviso:** todos os dados são fictícios e versionados em `fixtures/sessions.json`. Não há
> acesso ao backend do Practium, banco de dados real, envio de e-mail ou ação externa. A
> identidade por token de sessão é uma **simulação de vínculo de sessão**, não autenticação
> real e não oferece segurança de produção.

## 1. O que este servidor entrega

- Três tools **somente leitura**:
  - `get_user_context`
  - `check_onboarding_dependencies`
  - `get_recent_validation_errors`
- Identidade vinculada à sessão por um token de URL controlado pelo servidor. A agente não
  escolhe o usuário e um `user_id` divergente é rejeitado.
- Fixtures com quatro sessões e quatro usuários fictícios, cobrindo análise de solo ausente,
  erro de validação, indisponibilidade simulada e demonstração conjunta.
- Testes automatizados de cliente MCP contra o servidor e um smoke script.

## 2. Requisitos e instalação

- Node.js >= 18 (testado com Node 26.13.0).
- npm.

```bash
cd assistente-suporte-tecnico/practium-mcp-server
npm install
npm test
```

## 3. Execução local

```bash
npm start
# ou
PORT=3907 HOST=0.0.0.0 npm start
```

Endpoints:

| Caminho | Uso |
| --- | --- |
| `GET /healthz` | health check (não expõe tokens) |
| `GET /` | metadados do serviço |
| `/mcp/<session-token>` | endpoint MCP Streamable HTTP |

Exemplo:

```bash
curl -s http://127.0.0.1:3907/healthz
MCP_BASE_URL=http://127.0.0.1:3907/mcp/sim-session-gamma npm run smoke
```

### Variáveis de ambiente

| Variável | Padrão | Descrição |
| --- | --- | --- |
| `PORT` | `3907` | porta HTTP |
| `HOST` | `0.0.0.0` | interface de escuta |
| `MCP_FIXTURES_PATH` | `fixtures/sessions.json` | arquivo de fixtures sintéticas |
| `MCP_SESSION_TTL_MS` | `1800000` | TTL de sessões MCP ociosas (30 min) |

Não há segredos obrigatórios. As fixtures não contêm dados pessoais reais.

## 4. Deploy (endereço acessível pelo n8n)

O n8n roda em container/VPS; `localhost` do seu computador não é `localhost` do n8n. Para
que o nó `MCP Client Tool` alcance o servidor, publique-o em uma URL acessível pela instância
n8n. Este repositório inclui `Dockerfile` e `docker-compose.yml` prontos.

### Docker Compose local/rede

```bash
docker compose up --build -d
curl -s http://127.0.0.1:3907/healthz
```

### Deploy usado no T-007 (Dokploy)

O deploy de referência do T-007 foi feito como aplicação Docker no Dokploy, no mesmo
ambiente do n8n, construída a partir desta branch do repositório público:

- Repositório: `https://github.com/fathos82/N8N.git`
- Branch: `feature/T-007-practium-mcp-server-diagnostico-ativo`
- Build path/contexto: `assistente-suporte-tecnico/practium-mcp-server`
- Dockerfile: `Dockerfile`
- Porta: `3907`
- App Dokploy: `RYq2cdKcK2_o8IxAfDnkJ` (`practium-mcp-sim-vg0tti`)
- Endpoint público: `http://practium-mcp-sim-177-104-179-163.traefik.me`
- Endpoint MCP para o n8n: `http://practium-mcp-sim-177-104-179-163.traefik.me/mcp/sim-session-gamma`

> O deploy de referência usa HTTP simples no `*.traefik.me` porque só transporta fixtures
> sintéticas durante o teste. Para qualquer ambiente com dados reais, use TLS e autenticação
> real (T-008).

O domínio `*.traefik.me` resolve para o IP público da VPS e serve apenas para o ambiente de
teste. Para reproduzir em outro ambiente, troque o host pelo domínio/IP da sua instalação e
mantenha a porta `3907`.

> O servidor é de simulação e pode ficar exposto apenas durante os testes. Ele não guarda
> dados, não tem credenciais e não executa ações externas. Ainda assim, trate o token de
> sessão como um identificador de teste, não como segredo de produção.

## 5. Integração com o n8n

No n8n, use o nó **MCP Client Tool** (`@n8n/n8n-nodes-langchain.mcpClientTool`,
`typeVersion: 1.4`) conectado ao agente Flora em `ai_tool`:

| Campo | Valor |
| --- | --- |
| Endpoint | `http://<host>/mcp/sim-session-gamma` (use TLS em ambiente real) |
| Server Transport | `HTTP Streamable` |
| Authentication | `None` (a identidade vem do token de sessão na URL) |
| Tools to Include | `All` (as três tools são somente leitura) |
| Timeout | `30000` ms |

A cópia isolada do workflow é `[T-007] assistente-suporte-tecnico (MCP simulado)` e usa:

- `[T-007] knowledgeBase simulada` no lugar do sub-workflow real;
- `[T-007] Call Suporte (no-op)` no lugar do Call Suporte de produção;
- `Simple Memory` no lugar da memória Postgres;
- nenhum nó Postgres/Supabase/Google Drive/Mistral/Gmail;
- somente a credencial OpenAI para o modelo de chat.

Invoque pelo chat do n8n com o token `sim-session-gamma` para ver ao mesmo tempo a
dependência ausente e o erro de validação. Para trocar o cenário, troque o token na URL do
nó MCP (a identidade é definida pelo servidor, não pela agente).

### Workflows n8n criados no T-007

| Workflow | ID n8n | Estado | Papel |
| --- | --- | --- | --- |
| `[T-007] assistente-suporte-tecnico (MCP simulado)` | `GU2dSb6BGJlGJQRT` | **inativo** | cópia isolada da Flora com MCP |
| `[T-007] knowledgeBase simulada` | `PyjD9HpRTk3M3N2G` | ativo (sub-workflow) | retorno documental fictício |
| `[T-007] Call Suporte (no-op)` | `tCZfdm7LCk2MkarX` | ativo (sub-workflow) | escalonamento sem Postgres/Gmail |

Os dois sub-workflows precisam estar ativos para o nó `toolWorkflow` conseguir executá-los;
eles têm apenas trigger de sub-workflow e um nó Set, sem acesso externo. A cópia principal
fica **inativa** após os testes. Os exports sanitizados estão em
`workflows/T007-assistente-suporte-tecnico-mcp-simulado.json`,
`workflows/T007-knowledge-base-simulada.json` e `workflows/T007-call-suporte-noop.json`
(sem `shared`, `staticData` ou dados de conta).

## 6. Identidade simulada e limites

- O token fica no caminho `/mcp/<session-token>` ou no header `Authorization: Bearer <token>`.
- O servidor resolve o token para uma sessão e um `user_id` fixos nas fixtures.
- Cada sessão de transporte Streamable HTTP recebe um `mcp-session-id`; reutilizar esse ID
  contra outro token retorna `403` (`Identidade divergente`).
- Token desconhecido retorna `401` antes de qualquer tool.
- As tools aceitam `user_id` **apenas para testar rejeição**: se o valor divergir da sessão,
  retornam `isError: true` com `IDENTITY_MISMATCH` e nenhum dado.
- A agente é instruída a nunca enviar `user_id`.

**Limites explícitos:** isso não é autenticação, não valida credenciais, não emite token
assinado, não protege contra alguém que conheça a URL e não substitui OAuth/mTLS/validação
de tenant do T-008. O objetivo é exercitar o contrato e o fluxo de falha fechada.

## 7. Sessões e fixtures

Arquivo: `fixtures/sessions.json`.

| Token | Usuário fictício | Cenário |
| --- | --- | --- |
| `sim-session-alpha` | `user_ana_ficticia` | análise de solo ausente; sem erros de validação |
| `sim-session-beta` | `user_bruno_ficticio` | cadeia completa; erro de fósforo há 12 min |
| `sim-session-gamma` | `user_carla_ficticia` | dependência ausente **e** erro de fósforo (demonstração n8n) |
| `sim-session-degraded` | `user_diego_ficticio` | tools retornam `SIMULATED_BACKEND_UNAVAILABLE` |

Nenhum nome, fazenda, talhão ou erro corresponde a pessoa ou dado real. E-mails e
documentos não são usados. `occurred_minutes_ago` é convertido em `occurred_at` no momento da
consulta para que os erros permaneçam "recentes" de forma reproduzível.

## 8. Contrato das tools

Todas as respostas de sucesso incluem `simulated: true`, `contract_version: "T-007/0.1"`,
`data_source: "fixtures/sessions.json"` e um `disclaimer`.

### 8.1 `get_user_context`

Entrada:

```json
{ "user_id": "opcional, NÃO USAR — apenas teste de rejeição" }
```

Resposta:

```json
{
  "simulated": true,
  "session_label": "Caso 1 - análise de solo ausente",
  "user": {
    "user_id": "user_ana_ficticia",
    "display_name": "Ana Fictícia",
    "role": "gestor_business",
    "role_label": "Gestor de propriedade (business)",
    "plan": "business",
    "active_permissions": ["property:read", "field:read"]
  }
}
```

### 8.2 `check_onboarding_dependencies`

Entrada: `{}` (ou `user_id` apenas para teste de rejeição).

Resposta (resumida):

```json
{
  "simulated": true,
  "all_satisfied": false,
  "chain": [
    { "key": "property", "label": "Propriedade/Fazenda cadastrada", "status": "present" },
    { "key": "field", "label": "Talhão cadastrado na fazenda", "status": "present" },
    { "key": "soil_analysis", "label": "Análise de solo vinculada ao talhão", "status": "missing" },
    { "key": "fertilization_recommendation", "label": "Recomendação de adubação gerada", "status": "blocked", "depends_on": "soil_analysis" }
  ],
  "missing_steps": ["soil_analysis"],
  "blocked_steps": ["fertilization_recommendation"],
  "next_recommended_step": {
    "action": "orientar_cadastro",
    "target_step": "soil_analysis",
    "message": "Cadastre uma análise de solo ..."
  }
}
```

A cadeia é uma **hipótese de contrato** para o T-008; não afirma que o backend real usa
exatamente esses nomes, ordem ou regras.

### 8.3 `get_recent_validation_errors`

Entrada:

```json
{ "window_minutes": 60 }
```

`window_minutes`: inteiro de 1 a 1440; padrão 60.

Resposta:

```json
{
  "simulated": true,
  "window_minutes": 60,
  "count": 1,
  "errors": [
    {
      "id": "err-beta-001",
      "occurred_at": "2026-11-12T18:20:00.000Z",
      "occurred_minutes_ago": 12,
      "source": "frontend",
      "screen": "/analise-solo/novo",
      "field": "Fósforo (P)",
      "message": "Campo 'Fósforo (P)' deve ser numérico positivo.",
      "severity": "error"
    }
  ]
}
```

Sem erros na janela: `count: 0`, `errors: []` e uma nota orientando a não presumir a causa.

### 8.4 Erros

| Código | Quando | Efeito |
| --- | --- | --- |
| `IDENTITY_MISMATCH` | `user_id` da tool difere da sessão | `isError: true`, nenhum dado do usuário |
| `SIMULATED_BACKEND_UNAVAILABLE` | sessão `sim-session-degraded` | `isError: true`, nenhum diagnóstico |
| HTTP `401` | token de sessão desconhecido | handshake/tool não prossegue |
| HTTP `403` | `mcp-session-id` de um token usado em outro token | rejeitado antes de expor dados |
| HTTP `404` | caminho fora de `/mcp/<token>` | endpoint inexistente |

## 9. Testes

```bash
npm test
```

Cobertura (3 casos, teto do ticket):

1. `sim-session-alpha`: descoberta das três tools, perfil `gestor_business`, dependência
   `soil_analysis` ausente e nenhum erro de validação.
2. `sim-session-beta`: erro de fósforo retornado com campo/mensagem; `sim-session-degraded`
   retorna `SIMULATED_BACKEND_UNAVAILABLE` sem dados de diagnóstico.
3. Token desconhecido recebe `401`; `get_user_context` com `user_id` de outro usuário retorna
   `IDENTITY_MISMATCH` sem dados; `mcp-session-id` de alpha contra o token beta recebe `403`.

Smoke manual contra um servidor em execução:

```bash
npm run smoke
# ou
MCP_BASE_URL=http://<host>/mcp/sim-session-gamma npm run smoke
```

### Evidências executadas em 12/11/2026

- `npm test`: 3 testes passando, 0 falhas.
- `GET /healthz` no endpoint público: `{"status":"ok","mode":"simulated","contract_version":"T-007/0.1","sessions_configured":4,...}`.
- `npm run smoke` contra o endpoint público: descoberta das três tools e respostas simuladas
  de perfil, dependência ausente e erro de validação.
- Chat n8n (workflow `GU2dSb6BGJlGJQRT`):
  - dependência ausente: execução `37681` chamou `check_onboarding_dependencies` e respondeu que
    falta a análise de solo, marcando os dados como simulados;
  - perfil: execução `37692` chamou `get_user_context` e apresentou plano `profissional` e
    permissões simuladas;
  - erro de validação: execução `37677` chamou `get_recent_validation_errors` e devolveu o
    campo `Fósforo (P)` com a mensagem exata;
  - falha simulada: com `sim-session-degraded`, a Flora respondeu que a consulta estava
    indisponível e não inventou diagnóstico (endpoint restaurado para `gamma` depois);
  - `Call Suporte` no-op: execução `37686` retornou `status: simulated_noop` e nenhum e-mail
    foi enviado.
- Nenhum workflow de produção foi modificado ou ativado.

## 10. Isolamento de dados, credenciais e ações externas

- Todos os dados vêm de um JSON local versionado; não há banco nem API do Practium.
- O servidor não lê variáveis de ambiente de produção nem possui credenciais.
- As tools são somente leitura; não há tool de escrita, e-mail, webhook ou alteração de status.
- A cópia do n8n substitui o `Call Suporte` de produção por um sub-workflow no-op que apenas
  devolve uma mensagem de simulação, sem Postgres e sem Gmail.
- A cópia substitui a `knowledgeBase` real por uma base simulada e a memória Postgres por
  memória em buffer.
- A única chamada externa remanescente na cópia é o modelo OpenAI do agente, necessária para
  o chat. Nenhum workflow de produção é alterado ou ativado; a cópia T-007 permanece inativa.

## 11. Contrato e diferenças conhecidas para o T-008

O T-008 deve tratar, no mínimo:

1. **Autenticação real:** substituir o token de URL por identidade autenticada e verificável
   no servidor (sessão/OAuth/tenant), falhando fechado. A simulação não prova segurança.
2. **Fonte dos dados:** trocar o adaptador de fixtures por leitura autorizada à API oficial;
   confirmar nomes de campos, roles, planos, permissões e a cadeia real de onboarding.
3. **`role` e plano:** os valores `gestor_business`, `gestor_profissional`,
   `consultor_colaborador_business`, `free`, `profissional` e `business` são hipóteses.
4. **Erros de validação:** confirmar se existem logs de front-end/API, janela disponível,
   formato, paginação, limites e se dados sensíveis aparecem nas mensagens.
5. **Identidade e tenant:** validar usuário e tenant no servidor; nunca aceitar `user_id` do
   modelo/front-end. O campo `user_id` opcional das tools deve desaparecer ou virar
   verificação interna no T-008.
6. **Disponibilidade e falha:** manter `isError`/códigos estáveis e a instrução de não
   inventar diagnóstico; definir timeout, retry e fallback sem escalar dados entre tenants.
7. **Minimização e logs:** não registrar tokens, dados pessoais ou conteúdo sensível; revisar
   retenção e mascaramento.
8. **Transporte e deploy:** confirmar TLS, rede, allowlist e health check no ambiente real;
   o `*.traefik.me` é apenas teste.
9. **Separação de modos:** manter o modo simulado isolado e explicitamente rotulado; nunca
   apresentar fixtures como dados reais.
10. **Aprovação e homologação:** validar em ambiente autorizado antes de qualquer produção.

Consulte `arquiteture/06-practium-mcp-and-code-migration.md` e
`tickets/T-008-integracao-practium-mcp-backend-real.md`.
