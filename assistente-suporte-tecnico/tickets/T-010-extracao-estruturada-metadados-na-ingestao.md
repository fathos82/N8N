# T-010: [Futuro] Extração estruturada de metadados (Structured Outputs) na ingestão e filtro por Topic

**Status:** todo
**Depends on:** T-003
**Owner:** -

## Goal

Evoluir o nó `Generate Chunk Description` para utilizar **Structured Outputs (JSON Schema)** durante a ingestão, classificando automaticamente cada chunk com `topic`, `screen_path` e `keywords`, e reativar o filtro de `topic` na busca híbrida.

## Scope

- Referências arquiteturais: `arquiteture/03-ingestion-and-contextual-rag.md`, `arquiteture/01-retrieval-and-reranking.md`
- Arquivo `assistente-suporte-tecnico.json`:
  - Nó `Generate Chunk Description` retornando JSON estrito com `{ contextual_summary, topic, screen_path, is_tutorial }`
  - Nó `Setup Metadata` e `Default Data Loader1` gravando `topic` e `screen_path` dentro do JSONB `metadata` da tabela `documents_as`
  - Nó `knowledgeBase` reativando o parâmetro opcional `topic` enviado para `HibridySearchSuportAgent_v1.json`

## Out of scope

- Alterações no modelo de OCR da Mistral

## Acceptance criteria

- [ ] Todo chunk indexado em `documents_as` passa a conter `metadata.topic` preenchido com uma das categorias canônicas (`navegacao`, `cadastro`, `erro`, `planos_geral`) e `metadata.screen_path` (quando aplicável).
- [ ] A tool `knowledgeBase` permite filtrar opcionalmente por `topic` na RPC `hybrid_search_as` sem excluir resultados caso o tópico seja ambíguo (`topic = null`).

## Test budget: 2 new test cases (ceiling, not a target)

- Caso 1: Documento de cadastro de talhão indexado gera JSON válido e grava `metadata.topic = "cadastro"` no Supabase — positivo
- Caso 2: Busca com dúvida híbrida (navegação + cadastro) envia `topic = null` para não restringir indevidamente uma das intenções — negativo proposital

## Notes

<!-- O test-writer e o tech-lead anexam aqui evidências e bloqueios. -->
