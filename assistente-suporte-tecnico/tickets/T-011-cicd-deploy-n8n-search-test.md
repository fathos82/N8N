# T-011: Automatizar deploy do workflow de busca para cópia de teste do n8n

**Status:** in_progress
**Depends on:** T-001
**Owner:** implementor

## Goal

Permitir que alterações no `HibridySearchSuportAgent.json` sejam validadas e publicadas automaticamente na cópia de teste do workflow n8n quando forem enviadas a uma branch `feature/**`, sem atualizar o workflow de produção.

## Scope

- Referência arquitetural: `arquiteture/07-cicd-deploy-n8n-test.md`
- Arquivo `.github/workflows/deploy-n8n-test.yml` para validar o JSON e atualizar a cópia de teste via API pública do n8n.
- Incluir no Git o arquivo fonte `HibridySearchSuportAgent.json` necessário para a automação.
- Usar como destino somente a cópia de teste `HibridySearchSuportAgent (security copy)`, ID `9hLboYiaMlm9GKf6`.
- Ler URL e chave da API de variáveis/secrets do GitHub; nunca gravar credenciais no workflow ou no repositório.

## Out of scope

- Deploy para o workflow de produção `LyeROMlZEGlZXEEN`.
- Deploy do fluxo principal `assistente-suporte-tecnico` para a cópia `nl9lOKaIVfltHuZf`; seu JSON contém um header Bearer hardcoded e não deve ser enviado ao GitHub até ser higienizado.
- Publicação/ativação automática dos workflows no n8n.

## Acceptance criteria

- [ ] A GitHub Action roda em push para branches `feature/**` quando `HibridySearchSuportAgent.json` mudar.
- [ ] A Action valida que o arquivo é JSON válido antes de tentar deploy.
- [ ] O deploy atualiza somente o ID de teste `9hLboYiaMlm9GKf6`; o ID de produção não é usado como destino.
- [ ] Antes do `PUT`, a Action confirma que o alvo está inativo; se estiver ativo ou o estado for desconhecido, aborta sem atualizar.
- [ ] A autenticação usa secret do GitHub e não expõe a chave em logs, arquivos ou commits.
- [ ] O fluxo principal e seu ID de teste não são enviados nem alterados por esta Action.

## Test budget: 2 new test cases (ceiling, not a target)

- Caso 1: JSON válido no path monitorado é validado e encaminhado ao destino de teste — positivo.
- Caso 2: JSON inválido falha antes da chamada de deploy; a credencial não aparece nos logs — negativo proposital.

## Notes

<!-- O test-writer e o tech-lead anexam aqui evidências e bloqueios. -->

- Implementação enviada em `feature/T-011-n8n-cicd-test-deploy` (`7f4ff7e`, `1c0715b`, `92d3ed1`). A Action valida e atualiza somente a cópia de teste `9hLboYiaMlm9GKf6`; antes do `PUT`, consulta o alvo e recusa deploy se ativo/publicado ou se o estado for desconhecido. O fluxo principal não é incluído.
- Verificações locais: JSON válido; YAML parseável; sintaxe Bash válida; preparação do payload sem `id`/`active`; guarda de estado permite somente alvo inativo; ausência de `N8N_API_KEY` falha antes da chamada. Deploy ponta a ponta ainda depende de configurar `N8N_BASE_URL` como GitHub Actions variable e `N8N_API_KEY` como secret, e então executar a Action.
