# T-009: [Futuro] Implementar máquina de estados determinística para tutoriais passo a passo

**Status:** todo
**Depends on:** T-002, T-005
**Owner:** -

## Goal

Persistir no PostgreSQL o estado estruturado do tutorial em andamento (`active_doc_id`, `current_step`, `total_steps`, `steps_payload`) para garantir que o guia passo a passo nunca perca a posição, mesmo em conversas muito longas ou retomadas dias depois.

## Scope

- Referência arquitetural: `arquiteture/02-session-memory-and-context.md`
- Evolução da tabela `conversation_status` (ou tabela `conversation_tutorial_state`) no Postgres
- Criação de tools ou nós de controle de estado em `assistente-suporte-tecnico.json` para:
  - Iniciar um guia passo a passo salvando todas as etapas extraídas da `knowledgeBase`
  - Avançar `current_step + 1` mediante confirmação do usuário
  - Encerrar/limpar o estado quando `current_step == total_steps` ou quando o usuário mudar de assunto

## Out of scope

- Alterações no algoritmo de chunking ou OCR da ingestão

## Acceptance criteria

- [ ] Ao iniciar uma explicação passo a passo, o estado com a lista de etapas e `current_step = 1` fica salvo no Postgres associado ao `session_id`.
- [ ] Em cada nova mensagem da mesma sessão, o estado atual do tutorial é injetado no contexto da `Flora` sem precisar refazer a busca vetorial para os passos seguintes.
- [ ] Quando o usuário conclui a última etapa ou muda de assunto, o estado do tutorial é marcado como concluído.

## Test budget: 2 new test cases (ceiling, not a target)

- Caso 1: Tutorial de 7 etapas mantém progressão exata de `1` a `7` mesmo se o usuário fizer perguntas paralelas no meio do fluxo — positivo
- Caso 2: Usuário interrompe o tutorial no passo 2 para relatar outro problema urgente; a máquina de estados permite pausar/substituir o guia sem travar a conversa na etapa antiga — negativo proposital

## Notes

<!-- O test-writer e o tech-lead anexam aqui evidências e bloqueios. -->
