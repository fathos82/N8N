# Módulo 01: Retrieval, Context Window Expansion e Reranking

**Arquivo Alvo:** `HibridySearchSuportAgent_v1.json`  
**Workflow ID:** `LyeROMlZEGlZXEEN`  
**Consumidor Principal:** Tool `knowledgeBase` no workflow `assistente-suporte-tecnico.json`

---

## 1. Visão Geral do Módulo

Este módulo executa o pipeline de busca avançada (RAG) acionado pelo agente de suporte **Flora**. Ele combina busca híbrida no Supabase (semântica + textual com RRF), expansão de janela de contexto (busca de chunks vizinhos do mesmo documento) e reranking neural via Cross-Encoder da Cohere (`rerank-v4.0-fast`).

---

## 2. Estado Atual e Gargalos Identificados

1. **Descarte de Metadados no Retorno (`Return Sorted Itens`):**
   - O código atual retorna apenas strings formatadas como `[score] content`, descartando completamente o objeto `metadata` (`doc_id`, `file_name`, `chunk_index`, `chunk_total`, `allowedRoles`).
   - Isso impede o agente `Flora` de cumprir a instrução de seu System Prompt de *"elaborar a URL a partir de metadata"* ou saber de qual documento veio cada trecho.
2. **Corte Rígido Excessivo (`min_score_to_rank = 0.79`):**
   - No nó `Settings`, o parâmetro `min_score_to_rank` está em `0.79`. Consultas coloquiais de produtores rurais frequentemente obtêm scores entre `0.50` e `0.78` no Cohere Rerank e acabam descartadas, gerando respostas vazias e escalonamento prematuro para o suporte humano.
3. **Janela Curta e Desordenação de Passos (`window = 1`):**
   - O parâmetro `window` está em `1`, o que recupera apenas 1 chunk anterior e 1 posterior. Tutoriais de cadastro ou navegação com 4 ou 5 etapas ficam truncados.
   - Após o reranking da Cohere, os chunks retornam ordenados puramente por `relevance_score`, embaralhando a ordem lógica (`chunk_index`) de um passo a passo dentro do mesmo documento.
4. **Credencial Exposta em Header (`Trigger Hibirdy Search` e `Expand Context`):**
   - A chave `apikey` (`sb_publishable_...`) está declarada manualmente em texto claro nos headers HTTP, apesar do uso de `supabaseApi`.

---

## 3. Arquitetura Alvo (Refatoração Imediata)

### 3.1. Parâmetros do Nó `Settings`
- `limit`: `10` (quantidade inicial na busca híbrida)
- `top_k`: `7` (melhores hits para expansão de janela)
- `window`: `2` (expande 2 chunks antes e 2 depois no `get_chunks_by_index_as` para cobrir tutoriais completos)
- `min_score_to_expand`: `0.025` (score RRF mínimo para expandir)
- `min_score_to_rank`: `0.50` (piso mínimo de relevância no Cohere Rerank)
- `high_confidence_score`: `0.75` (limiar para classificar o resultado como `ALTA` vs `MEDIA` confiança)

### 3.2. Contrato de Saída do Nó `Return Sorted Itens`
O nó deve retornar um payload estruturado para o agente Flora contendo:
- Classificação de confiança (`ALTA` quando `relevance_score >= 0.75`, `MEDIA` quando `0.50 <= relevance_score < 0.75`).
- Agrupamento ou preservação de `metadata` (`doc_id`, `file_name`, `chunk_index`, `chunk_total`).
- Ordenação inteligente: preservar a prioridade dos documentos mais relevantes, mas garantir que chunks pertencentes ao mesmo `doc_id` tenham seu índice posicional explícito para não embaralhar tutoriais sequenciais.

---

## 4. Evolução Futura (Corrective RAG & Multi-Query)
- Caso `sortedDocuments` retorne vazio (`hasResults: false`), um sub-fluxo de **Query Rewriting** deverá gerar até 3 variações técnicas da pergunta do usuário (traduzindo termos coloquiais do campo para a terminologia do sistema Practium) e refazer a chamada à RPC `hybrid_search_as` antes de desistir.

---

## 5. Tickets Relacionados
- `tickets/T-001-enriquecer-retorno-busca-e-rerank.md`
- `tickets/T-006-corrective-rag-e-multi-query-expansion.md`
