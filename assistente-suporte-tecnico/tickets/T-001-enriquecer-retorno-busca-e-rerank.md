# T-001: Enriquecer retorno da busca híbrida com metadados, janela expandida e faixa de confiança

**Status:** done
**Depends on:** -
**Owner:** implementor

## Goal

Garantir que o sub-workflow de busca (`hibridy-search-suport-agent.json`) retorne os metadados completos de cada chunk (`doc_id`, `file_name`, `chunk_index`, `chunk_total`), amplie a janela de expansão (`window = 2`), ordene sequencialmente os passos de um mesmo documento e classifique os resultados por faixa de confiança (`ALTA` vs `MEDIA`).

## Scope

- Referência arquitetural: `arquiteture/01-retrieval-and-reranking.md`
- Arquivo `HibridySearchSuportAgent_v1.json`:
  - Nó `Settings` (ajuste de `window`, `min_score_to_rank` e inclusão de `high_confidence_score`)
  - Nó `Setup chunks` (garantia de deduplicação e ordenação posicional por `doc_id` e `chunk_index`)
  - Nó `Return Sorted Itens` (inclusão do objeto `metadata`, flag `hasResults`, nível de confiança `ALTA`/`MEDIA` e formatação estruturada para o LLM)

## Out of scope

- Alterações nas funções RPC do banco de dados Supabase (`hybrid_search_as` e `get_chunks_by_index_as`)
- Alterações no pipeline de ingestão de documentos em `assistente-suporte-tecnico.json`

## Acceptance criteria

- [x] O nó `Settings` define `window = 2`, `min_score_to_rank = 0.50` e `high_confidence_score = 0.75`.
- [x] O nó `Return Sorted Itens` inclui no payload retornado os metadados de cada chunk (`doc_id`, `file_name`, `chunk_index`, `chunk_total`) além do `content`, `score` e `confidence` (`ALTA` para score >= 0.75, `MEDIA` para 0.50 <= score < 0.75).
- [x] Chunks pertencentes ao mesmo `doc_id` aprovados no reranking preservam ou informam claramente sua ordem sequencial (`chunk_index`), evitando que um passo a passo chegue embaralhado ao agente.
- [x] Quando nenhum documento atingir `min_score_to_rank`, o retorno traz `hasResults: false` e `sortedDocuments: []` de forma estruturada.

## Test budget: 3 new test cases (ceiling, not a target)

- Caso 1: Busca com match semântico forte (`relevance_score >= 0.75`) retorna `hasResults: true`, `confidence: "ALTA"` e objeto `metadata` preservado — positivo
- Caso 2: Busca com termos coloquiais (`0.50 <= relevance_score < 0.75`) não é descartada e retorna `confidence: "MEDIA"` com chunks vizinhos (`window = 2`) ordenados por `chunk_index` — positivo
- Caso 3: Busca fora do domínio (`relevance_score < 0.50`) é filtrada e retorna `hasResults: false` e lista vazia — negativo proposital

## Notes

<!-- O test-writer e o tech-lead anexam aqui evidências e bloqueios. -->

- Implementação aplicada em `workflows/hibridy-search-suport-agent.json` na branch `feature/T-001-enriquecer-retorno-busca-e-rerank` (commit `d83af98`):
  - Nó `Settings`: `window = 2`, `min_score_to_expand = 0.025`, `min_score_to_rank = 0.50` (`0.5`) e `high_confidence_score = 0.75`.
  - Nó `Setup chunks`: deduplicação por `${docId}_${chunkIndex}` e ordenação posicional por `doc_id` e `chunk_index`.
  - Nó `Return Sorted Itens`: retorno estruturado `{ hasResults, sortedDocuments }` com `content`, `score`, `confidence` (`ALTA` / `MEDIA`), `metadata` completo (`doc_id`, `file_name`, `chunk_index`, `chunk_total`) e `formatted`, priorizando documentos por score máximo e ordenando chunks do mesmo `doc_id` sequencialmente por `chunk_index`.
- Verificações executadas: validação estrutural e de expressões via `tools.n8n.validate_workflow` (`valid: true`, `errorCount: 0`, `warningCount: 0`) e 3 casos de teste (Caso 1 `ALTA`, Caso 2 `MEDIA` com ordenação posicional, Caso 3 negativo com `hasResults: false` e `sortedDocuments: []`) validados com sucesso.
