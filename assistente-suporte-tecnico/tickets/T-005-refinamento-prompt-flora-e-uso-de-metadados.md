# T-005: Refinar System Prompt da Flora para uso de metadados, faixas de confiança e insumos multimodais

**Status:** done
**Depends on:** T-001, T-002, T-004
**Owner:** implementor

## Goal

Atualizar o System Prompt da agente `Flora` e a descrição da tool `knowledgeBase` para utilizar os metadados retornados na busca, respeitar o protocolo de confiança (`ALTA` vs `MEDIA`), numerar etapas do tutorial (`Passo X de Y`) e explorar proativamente as análises de print de tela e áudio.

## Scope

- Referência arquitetural: `arquiteture/05-agent-prompt-and-corrective-rag.md`
- Arquivo `assistente-suporte-tecnico.json`:
  - Nó `Flora` (`systemMessage`):
    - Regra de leitura de `[Análise da Imagem/Print enviado pelo usuário]` e `[Mensagem de áudio transcrita]`
    - Regra de decisão baseada em `confidence: "ALTA"` vs `confidence: "MEDIA"` e retentativa com reformulação quando `hasResults: false`
    - Numeração explícita de etapas (`Passo X de Y`) na entrega cadenciada
    - Uso seguro de `base_url` e `metadata` para compor links sem inventar URLs
  - Nó `knowledgeBase` (ajuste fino nas instruções do parâmetro `$fromAI('query', ...)` para incentivar queries ricas com termos técnicos e de erro extraídos do contexto/print)

## Out of scope

- Alteração do modelo base do agente (`gpt-4.1`)
- Alteração nos parâmetros da tool `Call Suporte`

## Acceptance criteria

- [x] O System Prompt da `Flora` contém instruções explícitas sobre como agir diante de resultados com `confidence: "ALTA"`, `confidence: "MEDIA"` e `hasResults: false`.
- [x] O System Prompt instrui a `Flora` a não perguntar novamente qual é a mensagem de erro caso ela já conste no bloco `[Análise da Imagem/Print enviado pelo usuário]`.
- [x] O POP exige numeração explícita do passo atual (`Passo X de Y`) durante a entrega em etapas para ancorar o progresso na memória.

## Test budget: 3 new test cases (ceiling, not a target)

- Caso 1: Diante de um print contendo a mensagem de erro, a Flora consulta imediatamente a `knowledgeBase` com o erro extraído sem pedir para o usuário digitar o erro — positivo
- Caso 2: Diante de retorno com `confidence: "MEDIA"`, a Flora confirma brevemente se o tópico corresponde à dúvida do usuário no Passo 1 — positivo
- Caso 3: Diante de retorno com `hasResults: false`, a Flora reformula a busca uma vez com termos alternativos e, persistindo vazio, não inventa procedimentos fora da base — negativo proposital

## Notes

<!-- O test-writer e o tech-lead anexam aqui evidências e bloqueios. -->

- Implementado na branch `feature/T-005-refinamento-prompt-flora-e-uso-de-metadados` (worktree limpo a partir de `HEAD` `5c76eca`), commit `276c13f`, com push confirmado em `origin`.
- Arquivo alterado: apenas `assistente-suporte-tecnico/workflows/assistente-suporte-tecnico.json` (`1 file changed, 2 insertions(+), 2 deletions(-)`).
- `Flora` (`systemMessage`) passou a conter: seção "Interpretação de Insumos Multimodais" (áudio/print usados imediatamente, sem repetir pergunta sobre erro visível), seção "Protocolo de Confiança da Busca" (`ALTA` >= 0.75 inicia direto; `MEDIA` 0.50–0.74 confirma o tópico; `hasResults: false` permite no máximo 1 reformulação e proíbe inventar procedimentos), POP com numeração obrigatória `Passo X de Y` e exemplos atualizados, além da regra de links seguros com `base_url` + rotas apenas quando explícitas no `metadata`/documento.
- `knowledgeBase`: descrição do `$fromAI('query', ...)` atualizada para exigir query rica com tema, termos técnicos do Practium, telas/campos e mensagem de erro exata extraída de contexto/áudio/print, com reformulação por sinônimos.
- Verificações: JSON válido, 98 nós e 98 IDs únicos, `git diff --check` limpo, sem segredos no diff/commit, `gpt-4.1` e `Call Suporte` preservados. `validate_workflow` (n8n MCP) retornou 1 erro e 3 warnings idênticos ao baseline `HEAD` (query de `getConverationStatus` sem prefixo `=`; warnings pré-existentes), sem regressões novas.
- Casos do test budget verificados estaticamente: Caso 1 (print com erro → consulta imediata, Exemplo 4), Caso 2 (`MEDIA` → confirmação no Passo 1, Exemplo 7) e Caso 3 (`hasResults: false` → 1 reformulação e nenhuma invenção, Exemplo 8).
- Limitação: não houve execução runtime real contra Postgres/OpenAI nem teste conversacional ao vivo; a evidência é estática/estrutural. O working tree principal possui alterações não commitadas do usuário e não foi tocado.
