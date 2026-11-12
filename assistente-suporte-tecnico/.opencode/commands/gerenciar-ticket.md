---
description: Seleciona, delega ao implementor e atualiza exatamente um ticket do quadro (sem agente ticket-lead)
---

Atue como **Tech Lead** para gerenciar **exatamente um ticket** deste projeto. Você gerencia o estado do ticket e o `tickets/BOARD.md`, enquanto toda a implementação técnica é delegada ao subagente `implementor`.

Argumento fornecido pelo usuário: `$ARGUMENTS`

## Fluxo obrigatório do Comando (Tech Lead)

1. **Seleção do ticket (apenas um por execução):**
   - Se `$ARGUMENTS` informar um ID `T-XXX`, trabalhe **somente** nesse ticket. Se o usuário passar mais de um ID, peça que escolha apenas um e pare.
   - Se `$ARGUMENTS` estiver vazio ou for `proximo`, leia `tickets/BOARD.md` e selecione o ticket com status `todo` elegível de menor número.

2. **Análise e verificação de elegibilidade:**
   - Leia o arquivo do ticket em `tickets/T-XXX-*.md`.
   - Leia os documentos de `arquiteture/` referenciados no ticket e verifique os tickets listados em `**Depends on:**` (e tickets relacionados).
   - Se alguma dependência não estiver `done`, não inicie o ticket: informe o impedimento ao usuário e mantenha o estado consistente.

3. **Marcação de início (`in_progress`):**
   - Antes de delegar, atualize `**Status:** in_progress` e `**Owner:** implementor` no arquivo do ticket.
   - Atualize `tickets/BOARD.md` movendo o ticket para a seção `## In progress` (`— \`in_progress\``).

4. **Delegação para o `implementor`:**
   - Acione a ferramenta `subagent` em modo **foreground** (`background: false`) com `agent: "implementor"`.
   - Passe ao `implementor` o ID e caminho do ticket, os documentos de arquitetura relevantes e instrua-o a implementar exclusivamente esse ticket em sua branch `feature/T-XXX-slug`, executar as verificações e fazer commit + push da branch para `origin` (sem merge na `main`).
   - **Nunca implemente o ticket diretamente** nesta sessão principal e nunca acione um segundo ticket na mesma chamada.

5. **Validação e atualização pós-execução (`done` ou `blocked`):**
   - Quando o `implementor` retornar, valide o relatório, o estado do Git/branch, o push em `origin`, os arquivos alterados e se todos os itens de `## Acceptance criteria` foram cumpridos:
     - **Se concluído e validado com sucesso:** marque os critérios atendidos no ticket, registre as evidências em `## Notes` (se necessário), atualize `**Status:** done` no ticket e mova-o para `## Done` (`- [x] ... — \`done\``) em `tickets/BOARD.md`. Em seguida, apresente o resumo ao usuário e pergunte se deseja fazer o merge da branch para a `main`.
     - **Se houve bloqueio (`blocked`):** garanta que o motivo, as evidências e o próximo passo estejam claros em `## Notes`, que `**Status:** blocked` esteja no arquivo do ticket e que o item esteja na seção `## Blocked` (`— \`blocked\``) em `tickets/BOARD.md`. Reporte o bloqueio ao usuário.
