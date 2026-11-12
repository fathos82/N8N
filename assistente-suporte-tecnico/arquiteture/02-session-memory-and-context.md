# Módulo 02: Gestão de Sessão, Memória Persistente e Contexto do Usuário

**Arquivo Alvo:** `assistente-suporte-tecnico.json`  
**Áreas do Canvas:** `Sesion Status Verification`, `Agent (Flora)`, e `Webhook /history`

---

## 1. Visão Geral do Módulo

Este módulo controla o ciclo de vida da sessão de atendimento entre o usuário da plataforma **Practium**, a agente de IA **Flora** e os atendentes humanos. Ele verifica o status da conversa no Postgres (`conversation_status`), aplica regras de TTL (`expires_at`), gerencia a memória de curto/médio prazo da conversa e injeta o papel (`role`) do usuário para controle de acesso (RBAC).

---

## 2. Estado Atual e Gargalos Identificados

1. **Memória Volátil e Janela Insuficiente (`Simple Memory` vs `Postgres Chat Memory`):**
   - O nó `Postgres Chat Memory` (`id: 234f0a77-634a-41c3-a365-bfda6ed91500`) existe no canvas, mas **não está conectado a nenhum nó**.
   - A agente `Flora` está conectada ao `Simple Memory` (`memoryBufferWindow` em memória RAM volátil) com `contextWindowLength: 3`.
   - O endpoint `Webhook (/history)` -> `Chat Memory Manager` também está conectado ao `Simple Memory1` (`contextWindowLength: 3`).
   - **Impacto:** Como a Flora entrega tutoriais **uma etapa por vez** (Paced Delivery), após 3 trocas de mensagens ela esquece o que foi retornado pela `knowledgeBase` no início do atendimento e perde o fio da meada.
2. **Hardcoding do `role` do Usuário (`Setup Role` e `extractSessionId`):**
   - O nó `Setup Role` define estaticamente `role = "gestor_business"`, ignorando qualquer `role` enviado no payload do chat trigger.
   - O nó `extractSessionId` possui uma atribuição com nome vazio (`name: ""`) recebendo `={{ $json.role }}`.

---

## 3. Arquitetura Alvo (Refatoração Imediata)

### 3.1. Persistência de Memória no Postgres
- Conectar o nó `Postgres Chat Memory` como provedor de memória (`ai_memory`) da agente `Flora` (e alinhar com a leitura de histórico se aplicável).
- Configurar `sessionIdKey` para usar consistentemente o `sessionID` extraído no nó `extractSessionId` (`={{ $('extractSessionId').item.json.sessionID }}`).
- Ampliar `contextWindowLength` para `12` interações, garantindo retenção completa de tutoriais multi-etapas.

### 3.2. Captura Dinâmica de `role` com Fallback Seguro
- No nó `Setup Role`, ler dinamicamente o papel enviado pelo cliente (`$json.role` ou `$json.metadata?.role`), mantendo `"gestor_business"` apenas como fallback padrão:
  `={{ $json.role || $json.metadata?.role || 'gestor_business' }}`
- No nó `extractSessionId`, nomear corretamente a propriedade `role` (`name: "role"`).

---

## 4. Evolução Futura (State Machine para Tutoriais Passo a Passo)
- Criar uma estrutura de estado persistida na tabela `conversation_status` (ou tabela auxiliar `conversation_step_state`) armazenando:
  - `active_guide_doc_id`
  - `current_step_index`
  - `total_steps`
  - `pending_steps_json`
- Isso permitirá que mesmo em conversas com mais de 20 interações ou retomadas horas depois, o agente saiba deterministicamente em qual passo do tutorial o usuário parou.

---

## 5. Tickets Relacionados
- `tickets/T-002-memoria-persistente-postgres-e-role-dinamico.md`
- `tickets/T-009-maquina-de-estados-para-tutoriais-passo-a-passo.md`
