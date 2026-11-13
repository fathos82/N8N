---
description: Baixa um fluxo do n8n e seus sub-workflows para uma pasta de projeto
---

Quero criar o projeto do fluxo "$ARGUMENTS" no repositório.

1. Descubra o ID exato:
   - Se `$ARGUMENTS` parece um ID (sem espaços, tipo `nl9lOKaIVfltHuZf`), use direto.
   - Senão, use a ferramenta de listagem de workflows do MCP do n8n e procure o nome exato (ignorando prefixos `[TEST]`). Se houver mais de um candidato, pare e pergunte qual é.
   - Nunca use uma cópia `[TEST]` como origem.
2. Rode no terminal do repositório:
   `python scripts/grab.py <ID>`
   O script baixa o fluxo e os sub-workflows que ele chama, cria a pasta com `workflows/*.json` e `project.json`, e redige segredos.
3. Mostre o resumo que o script imprimiu e rode `git status` para mostrar a nova pasta.

Não escreva os JSONs à mão: o MCP devolve o conteúdo para a conversa, e redigitar é a forma como já houve erros. O script usa a API REST, que é a fonte que grava os arquivos.

Não faça commit nem push sem pedido explícito.
