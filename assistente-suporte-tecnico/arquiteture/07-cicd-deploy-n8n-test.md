# Módulo 07: Deploy de workflows n8n para teste via GitHub Actions

## Objetivo

Validar e enviar mudanças de workflows exportados do repositório a uma cópia de teste do n8n através da API pública, acionadas por push em branches de feature. O fluxo de GitHub Actions deve manter a branch como fonte de trabalho e não publicar/ativar alterações automaticamente.

## Destino atual

- Base URL n8n: configurada em variável do GitHub Actions, nunca hardcoded como segredo.
- Workflow de busca de teste: `HibridySearchSuportAgent (security copy)`, ID `9hLboYiaMlm9GKf6`.
- Workflow de produção: `LyeROMlZEGlZXEEN` — proibido como destino da Action.

## Segurança e limites

- API key somente em GitHub Actions Secret; nunca salvar ou imprimir o valor.
- Validar o JSON antes de qualquer chamada à API.
- Na versão anterior (n8n 2.4.7), a API de atualização podia republicar um workflow ativo. A instância foi atualizada para `n8n 2.47.5` em 2026-11-12; antes do `PUT`, consultar o estado do alvo e falhar sem atualizar se estiver ativo/publicado ou se o estado não puder ser determinado.
- A Action não deve ativar/publicar workflows.
- O JSON `assistente-suporte-tecnico.json` não pode ser incluido neste deploy enquanto possuir Authorization Bearer hardcoded. O fluxo principal é fora de escopo deste módulo até higienização separada.
- A cópia de teste do fluxo principal, ID `nl9lOKaIVfltHuZf`, não é alvo deste deploy.

## Fluxo esperado

1. Push em `feature/**` com alteração em `HibridySearchSuportAgent.json` inicia a Action.
2. A Action verifica a validade do JSON.
3. A Action atualiza apenas o workflow de teste pelo endpoint de workflows da API do n8n, com autenticação fornecida pelo Secret.
4. Se o workflow de teste estiver ativo/publicado, ou se a API não permitir confirmar que está inativo, o job termina antes do `PUT`.
5. Falhas de validação/API deixam o job com erro e sem ativar o workflow.
