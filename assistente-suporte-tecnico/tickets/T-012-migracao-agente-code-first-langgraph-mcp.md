# T-012: [Futuro] Migração do núcleo do Agente Flora para arquitetura Code-First (LangGraph / Agent SDK + MCP)

**Status:** todo
**Depends on:** T-006, T-007, T-009
**Owner:** -

## Goal

Desacoplar o cérebro conversacional da agente Flora do JSON monolítico do n8n para um serviço agêntico versionado em código (TypeScript/Python com LangGraph, Mastra ou Claude Agent SDK), mantendo o n8n apenas como orquestrador de Webhooks, filas e ETL do Google Drive.

## Scope

- Referência arquitetural: `arquiteture/06-practium-mcp-and-code-migration.md`
- Criação de serviço agêntico em código com:
  - Grafo de execução explícito (Triagem Multimodal -> Diagnóstico MCP -> Busca Híbrida + Rerank -> Controle de Passo a Passo -> Validador Anti-Alucinação)
  - Persistência de estado (Checkpointer no Postgres/Supabase)
  - Suíte de testes automatizados de avaliação (Evals) com dataset de perguntas reais de produtores rurais
  - Observabilidade de traces, latência e custo de tokens (Langfuse / OpenTelemetry)

## Out of scope

- Desativação dos gatilhos do Google Drive no n8n (continuam operando via n8n)

## Acceptance criteria

- [ ] O serviço agêntico responde via endpoint HTTP/Streaming consumido pelo front-end ou pelo próprio n8n com latência inferior à cadeia atual de sub-workflows.
- [ ] Existe uma suíte de Evals automatizada com pelo menos 20 cenários de suporte do Practium validando fidelidade à base (faithfulness) e ausência de alucinação antes de cada deploy.
- [ ] Todo o código de prompts, tools MCP e máquina de estados está versionado em Git com CI/CD.

## Test budget: 3 new test cases (ceiling, not a target)

- Caso 1: Execução completa de fluxo multi-intenção (Navegação + Cadastro) via grafo mantém estado tipado e retorna resposta com streaming — positivo
- Caso 2: Suíte de regressão (Evals) aprova 100% dos casos de referência de suporte técnico do Practium — positivo
- Caso 3: Resposta gerada pelo modelo que tente citar uma tela ou botão inexistente no contexto recuperado é barrada pelo nó de Guardrail Anti-Alucinação — negativo proposital

## Notes

<!-- O test-writer e o tech-lead anexam aqui evidências e bloqueios. -->
