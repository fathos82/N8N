# T-003: Aprimorar Contextual Retrieval na ingestão e remover chaves de API hardcoded

**Status:** done
**Depends on:** -
**Owner:** implementor

## Goal

Enriquecer o prompt do nó `Generate Chunk Description` durante a ingestão de documentos para incluir categoria, tela/rota e sinônimos agrícolas no texto do chunk, e remover tokens de autenticação hardcoded nos nós HTTP da Mistral.

## Scope

- Referência arquitetural: `arquiteture/03-ingestion-and-contextual-rag.md`
- Arquivo `assistente-suporte-tecnico.json`:
  - Nó `Generate Chunk Description` (atualização do prompt enviado ao `gpt-4.1-mini` para extrair contexto situacional, categoria, caminho de tela e termos coloquiais do produtor rural)
  - Nós `Get Ocr Results`, `Uplod file to Mistral` e `Get Url Signed` (remoção de headers manuais `Authorization` redundantes ou com chave exposta em texto claro, mantendo a autenticação via credencial `httpBearerAuth`)

## Out of scope

- Alteração da lógica do `Recursive Markdown Text Splitter` no nó `Chunking`
- Alteração da estrutura de tabelas no Supabase (`documents_as` e `document_records_as`)

## Acceptance criteria

- [x] O prompt do nó `Generate Chunk Description` instrui o modelo a situar o chunk no documento informando funcionalidade/tela, categoria (Navegação, Cadastro, Erro, Planos) e sinônimos práticos de busca em português.
- [x] Nenhum nó HTTP da Mistral em `assistente-suporte-tecnico.json` contém chaves `Bearer ...` em texto claro nos parâmetros do nó.
- [x] A autenticação com a API da Mistral permanece configurada exclusivamente via credencial `httpBearerAuth` (`Bearer Auth Mistral account`).

## Test budget: 2 new test cases (ceiling, not a target)

- Caso 1: Ingestão de chunk sobre recomendação de adubação gera descrição contextual contendo módulo do sistema, categoria e termos correlatos em português — positivo
- Caso 2: Inspeção estática do JSON do workflow confirma ausência de tokens secretos hardcoded no header `Authorization` do nó `Get Ocr Results` — negativo proposital

## Notes

- Implementado na branch `feature/T-003-ingestao-contextual-enriquecida-e-seguranca`, commit `d16c91d9957f8e77a376e1f7395436d282bccb5f`, com push confirmado em `origin`.
- Validação estática: JSON válido, 92 nós, contrato downstream preservado e diff limitado a `assistente-suporte-tecnico/workflows/assistente-suporte-tecnico.json`.
- Validação do prompt: presença de funcionalidade/seção, categorias `Navegação`, `Cadastro`, `Erro` e `Planos`, tela/caminho sem inventar URL, sinônimos e vocabulário agrícola.
- Validação de segurança: `Uplod file to Mistral`, `Get Url Signed` e `Get Ocr Results` sem `headerParameters`/`Authorization` manual e com `httpBearerAuth` (`Bearer Auth Mistral account`).
- Validação MCP dos nós alterados: `valid: true`; `git diff --check`: passou.
- Observação operacional: a chave Mistral historicamente exposta ainda deve ser rotacionada na conta/provider, fora do repositório.
