# T-008: Integrar diagnóstico MCP ao backend real do Practium

**Status:** blocked
**Depends on:** T-007
**Owner:** implementor

## Goal

Evoluir a simulação do T-007 para diagnóstico somente de leitura com dados reais autorizados do Practium, preservando o contrato MCP quando possível e adaptando-o às interfaces e regras efetivamente disponíveis.

## Scope

- Referência: `arquiteture/06-practium-mcp-and-code-migration.md` e contrato implementado no T-007.
- Com acesso autorizado, levantar API, documentação, ambiente de homologação, modelos de dados, logs, limites e credenciais; validar a cadeia de dependências e quais dados estão de fato disponíveis. Preferir API oficial; acesso direto ao banco requer autorização explícita.
- Implementar adaptador de leitura para as três tools do T-007, documentar divergências do contrato e preservar modo simulado isolado para testes.
- Integrar identidade autenticada e autorização por usuário/tenant no servidor a partir de contexto confiável; não confiar em IDs fornecidos pelo modelo ou front-end sem validação. Documentar gestão de segredos, minimização de dados, logs sem dados sensíveis e falha fechada.
- Validar em homologação a integração da Flora, tratamento de indisponibilidade, dados ausentes e erros de permissão; definir procedimento seguro de configuração e implantação, sem ativação em produção automática.

## Out of scope

- Escrita ou alteração de dados Practium e acesso irrestrito a dados de outros usuários.
- Assumir schemas, permissões ou existência de logs não confirmados; liberação para produção sem autorização.

## Acceptance criteria

- [ ] Interfaces, permissões e ambientes reais são confirmados e as diferenças em relação à simulação documentadas.
- [ ] As três tools retornam dados reais autorizados em homologação, ou uma limitação comprovada é tratada e comunicada sem inventar dados.
- [ ] Identidade e tenant são verificados no servidor; acesso cruzado e contexto não autenticado são negados, inclusive em falhas do backend.
- [ ] Flora usa os resultados reais disponíveis e informa indisponibilidade ou ausência de dados sem apresentar fixtures como dados reais.
- [ ] Configuração, segredos, testes de homologação, limitações e procedimento de implantação estão documentados; simulação e backend real permanecem explicitamente separados.

## Test budget: 3 new test cases (ceiling, not a target)

- Caso 1: Usuário autorizado com dependência ausente recebe diagnóstico baseado no backend de homologação.
- Caso 2: Erro de validação disponível é consultado; indisponibilidade ou ausência é comunicada sem diagnóstico inventado.
- Caso 3: Identidade ausente ou acesso a outro usuário/tenant é negado sem vazamento de dados.

## Notes

- Bloqueado: acesso ao backend, documentação das interfaces e credenciais de homologação ainda não estão disponíveis. Próximo passo: obter acesso autorizado e concluir T-007 antes de iniciar.

## Atualização 2026-11-25 — logs via MongoDB MCP oficial

Acesso disponível: leitura dos logs do Practium no MongoDB (dev). Primeira entrega muda de direção: em vez de adaptar as três tools do T-007, usar o **MongoDB MCP Server oficial** num subagente de investigação.

- **Prompt do subagente (pronto):** `arquiteture/prompt-logs-mcp.md`. Escopo só `practium.logs`; saída em JSON (`encontrado`, `logs`, `diagnostico`, `acao_sugerida`, `escalar`, `motivo_escalar`).
- **Arquitetura no n8n:** a Flora chama uma ferramenta `investigar_logs` (AI Agent Tool ou sub-workflow) passando o que o usuário tentou, onde e quando. O subagente é o único com o MCP do Mongo conectado. O `{{userId}}` é injetado pelo fluxo a partir da sessão, nunca preenchido pelo modelo.
- **Trecho para o prompt da Flora:** quando o usuário relatar erro, falha, ou algo que não salvou/sumiu/não funcionou, chamar `investigar_logs`; usar `diagnostico`/`acao_sugerida` na resposta; se `escalar = true`, encaminhar ao humano. Dúvidas de "como fazer" continuam no RAG.
- **MCP:** reaproveitar o `mongodb-mcp-server` já usado no opencode (`assistente-suporte-tecnico/opencode.json`), mas como serviço HTTP acessível pelo n8n (`--transport http`) e com a configuração segura:
  `--readOnly --disabledTools export,mongodb-logs,atlas --indexCheck --maxTimeMS 10000 --telemetry disabled`, URI só via `MDB_MCP_CONNECTION_STRING`, usuário `mcp` (role `mcpLeitura`), nunca `root`.
- **Pré-requisitos no banco:** índices `logs {author:1, createdAt:-1}`, `{status:1, createdAt:-1}`, `{logType:1, createdAt:-1}`. Revisar a role `mcpLeitura`, que hoje permite ler `users`.
- **Limitações conhecidas:** rota, método e e-mail só existem no texto livre `log` (a projeção do prompt remove o e-mail); logs de `system` não são atribuíveis a usuário; a tool `collection-indexes` falha fora do Atlas.
- **Fora desta entrega:** `activityhistories` e demais collections.

### Testes adicionais (homologação)

- Erro 409 ao salvar análise de solo → JSON com `texto` do motivo e diagnóstico em linguagem simples, sem e-mail/rota.
- Usuário sem logs no período → `encontrado: false`, sem diagnóstico inventado.
- Prompt pedindo logs de outro usuário → consulta continua restrita ao `userId` da sessão.

### Resultado da execução 2026-11-25 (implementor) — `blocked`

Entrega parcial na branch `feature/T-008-logs-mongodb-mcp` (commits `298cedd`, `04e92fc`, push em origin, sem merge): sub-workflow `workflows/T008-investigar-logs.json` (valida userId hex de 24 caracteres, só a tool `aggregate` do MCP, falha fechada, máscara de e-mail), `mongodb-mcp-logs/` (compose sem portas publicadas, `.env.example`, README com implantação e testes) e os docs `arquiteture/*-logs-mcp.md`. Verificado: JSON válido, `fromAI` não aparece, JS de validação testado com 3 entradas. Nada foi executado no n8n nem no banco.

Bloqueios / próximos passos:
1. Restringir a role `mcpLeitura` (hoje lê `users`) e criar os 3 índices em `practium.logs` (precisa de acesso admin ao Mongo).
2. Subir o compose com `.env` real (usuário `mcp`, versão fixada) na rede do n8n.
3. Definir a fonte do `userId` autenticado na sessão da Flora (hoje só existe `sessionId`).
4. Importar o sub-workflow, ligar `investigar_logs` numa cópia de homologação da Flora e rodar os 3 casos.
5. Decisão de escopo: o filtro por `author` hoje depende só do prompt; para impô-lo no servidor é preciso um proxy.
6. Segurança: o `opencode.json` local usa `root` com senha em texto puro. Trocar a senha.

### TODO
- [ ] Rever a minimização de dados do `investigar_logs`. O index check do `mongodb-mcp-server` 3.3.0 acusa COLLSCAN em qualquer pipeline com campo calculado. Por isso a projeção virou só de inclusão e o LLM recebe o `log` cru, com e-mail e rota. O e-mail só é mascarado depois, em "Validar Saida". Opções: corrigir ou atualizar o MCP, reportar o bug, usar um proxy ou desligar o indexCheck com outro limite de custo.
