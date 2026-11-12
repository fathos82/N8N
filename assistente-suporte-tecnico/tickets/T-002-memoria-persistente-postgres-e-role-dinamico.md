# T-002: Conectar memória persistente no Postgres e capturar role dinâmico do usuário

**Status:** done
**Depends on:** -
**Owner:** -

## Goal

Persistir a memória de conversação da agente Flora no PostgreSQL com janela de 12 interações (substituindo a memória volátil de 3 mensagens) e tornar dinâmica a leitura do papel (`role`) do usuário na entrada do chat.

## Scope

- Referência arquitetural: `arquiteture/02-session-memory-and-context.md`
- Arquivo `assistente-suporte-tecnico.json`:
  - Nó `Postgres Chat Memory` (conexão `ai_memory` ao nó `Flora`, configuração de `sessionIdKey` e `contextWindowLength: 12`)
  - Nó `Simple Memory` e `Simple Memory1` (ajuste de janela e substituição pela memória persistente no agente principal)
  - Nó `Setup Role` (leitura dinâmica de `$json.role || $json.metadata?.role || 'gestor_business'`)
  - Nó `extractSessionId` (correção do campo de atribuição com nome vazio `""` para `"role"`)

## Out of scope

- Criação de novas tabelas SQL fora do padrão já utilizado pelo nó `memoryPostgresChat` e `conversation_status`
- Alterações no sub-workflow `Call Suporte`

## Acceptance criteria

- [x] O nó `Postgres Chat Memory` está conectado à entrada `ai_memory` do agente `Flora` com `contextWindowLength` configurado para `12` e chave de sessão vinculada ao `sessionID` da conversa.
- [x] O nó `Setup Role` utiliza expressão dinâmica com fallback seguro para `"gestor_business"` caso o payload inicial não envie `role`.
- [x] O nó `extractSessionId` atribui corretamente a variável `role` (sem chave vazia `""`) e a repassa no fluxo.

## Test budget: 3 new test cases (ceiling, not a target)

- Caso 1: Conversa com mais de 4 etapas de confirmação mantém o contexto do tutorial inicial através do `Postgres Chat Memory` — positivo
- Caso 2: Payload de entrada contendo `role: "produtor_independente"` preserva esse papel até a chamada da tool `knowledgeBase` — positivo
- Caso 3: Payload de entrada omitindo o campo `role` assume automaticamente o fallback `"gestor_business"` sem quebrar a expressão — negativo proposital

## Notes

<!-- O test-writer e o tech-lead anexam aqui evidências e bloqueios. -->

- Implementação publicada na branch `feature/T-002-memoria-persistente-postgres-e-role-dinamico` (commit `e2286a5`) em `workflows/assistente-suporte-tecnico.json`:
  - Nó `Postgres Chat Memory` conectado à entrada `ai_memory` de `Flora`, configurado com `sessionIdType: "customKey"`, `sessionKey`/`sessionIdKey: "={{ $('extractSessionId').item.json.sessionID }}"` e `contextWindowLength: 12`.
  - Nós `Simple Memory` e `Simple Memory1` ajustados para `contextWindowLength: 12` e conexão do agente principal substituída pela memória persistente no Postgres.
  - Nó `Setup Role` atualizado para expressão dinâmica `={{ $json.role || $json.metadata?.role || 'gestor_business' }}`.
  - Nó `extractSessionId` corrigido com `name: "role"` (removendo a chave vazia `""`).
- Verificações executadas (todas **estáticas**, sem runtime):
  - Validação sintática JSON (`python3 -m json.tool workflows/assistente-suporte-tecnico.json`).
  - Validação de schema dos nós via `n8n` MCP (`validate_node` para `memoryPostgresChat`, `memoryBufferWindow` e `set`): confirma que os campos usados (`sessionIdType: "customKey"`, `sessionKey`, `contextWindowLength`) existem e são aceitos nas versões dos nodes em uso.
  - Asserções automatizadas da topologia/conexões e simulação dos Casos 2 e 3 (`role: "produtor_independente"`, `metadata.role` e fallback `"gestor_business"`).
- **Pendências — validação comportamental em runtime (não executada neste ambiente):**
  - Os 3 casos de teste do budget exigem a instância n8n real conectada ao Postgres; aqui só houve verificação estática. O que falta fazer:
    1. **Importar o JSON atualizado** na cópia de teste `nl9lOKaIVfltHuZf` (`assistente-suporte-tecnico (security copy)`) e conferir que a credencial `Postgres account` resolve.
    2. **Caso 1 (positivo):** abrir o chat da Flora, iniciar um tutorial e fazer 5+ trocas de mensagem (confirmações de etapa); confirmar que a Flora ainda lembra da etapa 1 e que as mensagens aparecem na tabela `n8n_chat_histories` do Postgres. O node cria a tabela automaticamente se ela não existir, mas em banco gerenciado (Supabase) vale confirmar permissão de DDL do usuário da credencial.
    3. **Caso 2 (positivo):** enviar payload com `role: "produtor_independente"` e inspecionar a execução do sub-workflow `knowledgeBase` (`9hLboYiaMlm9GKf6`), conferindo que o input `role` chegou como `produtor_independente` (não como `gestor_business`).
    4. **Caso 3 (negativo proposital):** enviar payload sem `role` (e sem `metadata.role`), conferir que a expressão do `Setup Role` não quebra e que a `knowledgeBase` recebe `gestor_business`.
  - Próximo passo para desbloquear: executar os 3 casos na cópia de teste do n8n (manualmente ou via `n8n_test_workflow` do MCP, se a instância estiver acessível ao servidor MCP).
- Observação de escopo: o node `Simple Memory` ficou no canvas **sem conexões** (órfão), conforme o ticket — a substituição pela memória persistente vale para o agente principal; a branch `Webhook (/history) → Chat Memory Manager → Simple Memory1` não faz parte deste escopo (ver `arquiteture/02-session-memory-and-context.md` §3.1 "se aplicável").
