# T-006: [Futuro] Implementar Corrective RAG e Multi-Query Expansion no sub-workflow de busca

**Status:** todo
**Depends on:** T-001
**Owner:** -

## Goal

Adicionar uma camada de **Corrective RAG (CRAG)** e **Multi-Query Expansion** no `HibridySearchSuportAgent_v1.json` para reescrever automaticamente queries coloquiais do produtor rural em termos técnicos do sistema Practium quando a busca inicial tiver baixa relevância.

## Scope

- Referências arquiteturais: `arquiteture/01-retrieval-and-reranking.md`, `arquiteture/05-agent-prompt-and-corrective-rag.md`
- Arquivo `HibridySearchSuportAgent_v1.json`:
  - Nó avaliador pós-Rerank que verifica se `max(relevance_score) < 0.50`
  - Sub-fluxo de *Query Rewriting* com `gpt-4.1-mini` traduzindo gírias/termos de campo (ex: *"jogar calcário"*, *"terra ácida"*, *"lançar saca"*) para os termos dos manuais do Practium
  - Loop controlado (máximo de 1 retentativa automática) antes de retornar `hasResults: false`

## Out of scope

- Alterações no fluxo de atendimento humano (`Call Suporte`)
- Alterações no pipeline de OCR da Mistral

## Acceptance criteria

- [ ] Quando a primeira busca no Cohere Rerank não produzir nenhum resultado com `relevance_score >= 0.50`, o workflow aciona automaticamente o reescritor de query (máximo 1 vez por chamada).
- [ ] O reescritor gera até 3 variações semânticas alinhadas ao vocabulário da plataforma Practium e executa a busca híbrida combinada.
- [ ] O tempo total adicional em caso de fallback não excede 3 segundos e previne loops infinitos.

## Test budget: 2 new test cases (ceiling, not a target)

- Caso 1: Pergunta com jargão coloquial que falha na primeira busca é reescrita automaticamente e recupera o documento correto na segunda tentativa — positivo
- Caso 2: Pergunta completamente alheia ao sistema Practium falha na primeira e na segunda tentativa e encerra sem entrar em loop infinito — negativo proposital

## Notes

<!-- O test-writer e o tech-lead anexam aqui evidências e bloqueios. -->
