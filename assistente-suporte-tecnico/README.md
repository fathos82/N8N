# assistente-suporte-tecnico (Flora / Practium)

Agente de suporte (chat) com RAG. Origem: workflow n8n `nl9lOKaIVfltHuZf` ("security copy").

## Blocos do workflow
- **Chat**: Chat Trigger -> Setup Role -> Settings (base_url) -> extractSessionId -> status da conversa (Postgres `conversation_status`: bot_active / wait_human / human_active, com TTL) -> agente **Flora** (GPT-4.1, memória Postgres, tools: knowledgeBase, Think, Call Suporte).
- **Ingestão RAG**: Drive triggers / Webhook -> roteia por tipo (MD/TXT, HTML, OCR Mistral) -> hash (record manager no Supabase) -> chunking -> contexto por chunk (gpt-4.1-mini) -> embeddings -> Supabase `documents_as`.
- **Remoção**: trigger de Drive -> apaga chunks, registro e arquivo.

## Pendências de segurança
- O nó **Get Ocr Results** tem a chave da Mistral escrita direto no header Authorization. Trocar para a credencial `Bearer Auth Mistral account` e **revogar/rotacionar a chave**.
- Webhook de chat com `allowedOrigins: *`.

## Pasta
- `workflows/`: JSON exportados (nunca commitar segredos).

## Fluxos dependentes (verificados em 11/11/2026)

### 1. knowledgeBase -> `9hLboYiaMlm9GKf6` (HibridySearchSuportAgent, security copy, inativo, 14 nós)
Sub-workflow chamado pela tool `knowledgeBase`. Entradas: `query`, `topic`, `role`.
Fluxo: embedding da query (OpenAI text-embedding-3-small) -> busca híbrida (RPC Supabase `hybrid_search_as`, filtra por `allowedRoles`) -> expansão de contexto (RPC `get_chunks_by_index_as`, janela 1) -> rerank Cohere `rerank-v4.0-fast` -> devolve `sortedDocuments` com score >= 0.79.
- Credenciais: OpenAi, Supabase, CohereApi.
- A `apikey` publishable do Supabase está escrita nos headers de 2 nós (baixo risco, mas melhor mover para a credencial).
- Tem `pinData` de teste (role `consultor_colaborador_business`).

### 2. Call Suporte -> `B5_8SFTkZxmXrcWOp0Gg1` (ATIVO, 4 nós, versão 155)
Chamado pela tool `Call Suporte`. Entradas: `tittle`, `abstract`, `sesseionID` (grafia com erro, mantida porque é o contrato).
Fluxo: Postgres `conversation_status` -> `wait_human`, `expires_at` = agora + 10 min -> Gmail para os e-mails de suporte -> retorna "requisição aberta".
- **Atenção:** a cópia do agente aponta para o Call Suporte **de produção**. Testar a cópia grava no mesmo banco e envia e-mail real.
- Destinatários de e-mail escritos direto no nó.

### Dados externos compartilhados
Postgres (`conversation_status`, memória do chat), Supabase (`documents_as`, `document_records_as`), Google Drive (pasta `N8N_PRACTIUM_AS`), Mistral OCR, OpenAI, Cohere, Gmail.

### Observações
- O nó `Setup Role` do agente fixa `role = gestor_business`; o nó `Set Wait Human Response` não tem saída conectada.
- A cópia não é independente: IDs de sub-workflows (`9hLb...` copiado, `B5_8...` original) precisam ser ajustados se o projeto for implantado em outra instância.
