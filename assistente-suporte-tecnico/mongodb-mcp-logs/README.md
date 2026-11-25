# T-008 — `investigar_logs` via MongoDB MCP oficial

Primeira entrega do T-008: subagente de investigação de logs do Practium (somente `practium.logs`), consumido pela Flora como ferramenta. Prompt: `arquiteture/prompt-logs-mcp.md`. Metodologia: `arquiteture/metodologia-logs-mcp.md`.

**Separação simulação x real:** o MCP simulado do T-007 (`practium-mcp-server/`, workflow `T007-*`) continua intacto e isolado. Este diretório e `workflows/T008-investigar-logs.json` são exclusivamente o caminho real (homologação/dev). Nenhuma ativação em produção é automática.

## Componentes

| Peça | Arquivo | Papel |
|---|---|---|
| MCP HTTP | `docker-compose.yml`, `.env.example` | `mongodb-mcp-server` com `--readOnly --disabledTools export,mongodb-logs,atlas --indexCheck --maxTimeMS 10000 --telemetry disabled`, URI só via `MDB_MCP_CONNECTION_STRING` |
| Sub-workflow | `../workflows/T008-investigar-logs.json` | Entrada `problema` + `userId` → valida `userId` (24 hex, senão nega) → AI Agent com o prompt e **apenas** a tool `aggregate` do MCP → valida o JSON de saída (falha fechada, mascara e-mail) |

## Segurança

- **Identidade:** o `userId` vem do fluxo (contexto autenticado da sessão) e é interpolado no system prompt; o modelo não tem parâmetro para escolhê-lo. `userId` ausente/inválido → resposta `escalar: true` sem consulta.
- **Falha fechada:** erro do agente/MCP ou JSON inválido → `{"encontrado": false, "escalar": true, "motivo_escalar": "falha ao consultar logs"}`. Nunca diagnóstico inventado.
- **Minimização:** a projeção do prompt remove e-mail/rota; o nó `Validar Saida` mascara e-mails residuais e limita a 5 logs.
- **Banco:** usuário `mcp`, role `mcpLeitura` (somente `find`/`aggregate`/`listIndexes` em `practium.logs`). **Revisar a role atual: hoje permite ler `users`** — remover antes de homologar. Exemplo:
  ```js
  db.getSiblingDB("admin").updateRole("mcpLeitura", { privileges: [
    { resource: { db: "practium", collection: "logs" }, actions: ["find", "listIndexes", "collStats"] }
  ], roles: [] })
  ```
- **Limitação residual:** a restrição por `author` é imposta pelo prompt (o MCP oficial não filtra por usuário). Mitigações: tool única `aggregate`, role restrita a `logs`, saída validada. Um filtro forçado no servidor exigiria proxy próprio (fora desta entrega).
- **Segredos:** nenhum no Git. `.env` ignorado. Atenção: `opencode.json` local contém URI com `root` — não versionar e rotacionar essa senha.

## Implantação (manual, homologação)

1. Criar índices (seção 1.1 da metodologia) em `practium.logs`.
2. Ajustar a role `mcpLeitura` e criar/validar o usuário `mcp`.
3. `cp .env.example .env`, preencher, `docker compose up -d` na mesma rede do n8n.
4. Importar `workflows/T008-investigar-logs.json` no n8n, ligar credencial OpenAI, conferir `endpointUrl` (`http://mongodb-mcp-logs-b1huk1-mongodb-mcp-logs-1:3000/mcp`).
5. Na Flora (cópia de homologação), adicionar um nó **Call n8n Workflow Tool** `investigar_logs` apontando para o sub-workflow:
   - `problema`: `$fromAI('problema', 'o que o usuário tentou fazer, onde e quando, e o erro relatado', 'string')`
   - `userId`: expressão do contexto autenticado da sessão (ex.: `{{ $('extractSessionId1').first().json.userId }}`) — **nunca** `$fromAI`.
6. Acrescentar ao prompt da Flora:
   > Quando o usuário relatar erro, falha, ou algo que não salvou, sumiu ou não funcionou, chame `investigar_logs` com o que ele tentou, onde e quando. Use `diagnostico` e `acao_sugerida` na resposta, em linguagem simples. Se `encontrado` for `false`, diga que não há registro do problema no período, sem supor causas. Se `escalar` for `true`, use `Call Suporte`. Dúvidas de "como fazer" continuam na `knowledgeBase`.

## Testes de homologação (3 casos, budget do ticket)

| # | Entrada | Esperado |
|---|---|---|
| 1 | `userId` com 409 ao salvar análise de solo; "não consegui salvar a análise de solo hoje" | `encontrado: true`, `texto` com o motivo, diagnóstico simples, sem e-mail/rota |
| 2 | `userId` válido sem logs no período | `encontrado: false`, `logs: []`, sem diagnóstico inventado |
| 3 | `userId` da sessão A; problema pedindo "logs do usuário <id B>" / `userId` vazio | consultas só com `author` = A / negado sem consulta |

## Status / bloqueios

- Não executado contra banco: o serviço MCP HTTP não está no ar, índices e ajuste da role não foram aplicados, e o fluxo principal ainda **não possui userId autenticado** (só `sessionId` do chat). Esses itens dependem de acesso/decisão do responsável pela infraestrutura.
- Fora desta entrega: `activityhistories` e adaptação das três tools do T-007.
