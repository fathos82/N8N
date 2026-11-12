# T-007: Simular diagnóstico ativo da Flora com servidor MCP local

**Status:** done
**Depends on:** T-005
**Owner:** implementor

## Goal

Experimentar o diagnóstico ativo de ponta a ponta sem acesso ao backend Practium: criar um servidor MCP real com dados fictícios e conectá-lo a uma cópia de teste da Flora no n8n. A simulação deve exercitar o mesmo contrato que será adaptado ao backend real no T-008, sem afirmar que os dados ou a autenticação são reais.

## Scope

- Referência arquitetural e contrato inicial: `arquiteture/06-practium-mcp-and-code-migration.md`.
- Criar um servidor MCP local, usando SDK MCP e transporte compatível com a versão instalada do n8n; documentar inicialização, dependências, endereço acessível pelo n8n e configuração. Não substituir MCP por uma API HTTP comum.
- Expor tools somente de leitura `get_user_context`, `check_onboarding_dependencies` e `get_recent_validation_errors` sobre fixtures sintéticas versionadas, incluindo pelo menos dois usuários/sessões, dependência ausente e erro de validação. Documentar schemas, respostas, erros e limitações do contrato proposto.
- Integrar as tools à Flora numa cópia isolada do workflow; ajustar instruções da agente para escolher ferramentas, usar o resultado no diagnóstico, distinguir simulação de dados reais e responder com cautela quando a consulta falhar ou não houver dados.
- Simular identidade vinculada à sessão em configuração de teste controlada pelo servidor; rejeitar identidade ausente, desconhecida ou divergente, sem confiar em `user_id` arbitrário fornecido pela agente. Documentar que isso não constitui autenticação real.
- Documentar como reproduzir os testes completos e como impedir que a simulação acesse serviços reais ou dispare ações externas, incluindo `Call Suporte`.

## Out of scope

- Acesso, credenciais ou integração ao backend real; implantação em produção; alegar segurança de produção.
- Tools de escrita, dados pessoais reais ou alterações na ingestão.
- Modificar/ativar workflows de produção ou enviar e-mails reais durante os testes.

## Acceptance criteria

- [x] O servidor inicia localmente conforme documentação e um cliente MCP consegue descobrir e invocar as três tools com schemas e respostas documentados.
- [x] A cópia isolada da Flora consulta as tools via MCP e apresenta como simulados o perfil, a dependência ausente e o erro de validação obtidos das fixtures, sem inventar resultados quando a consulta falha.
- [x] Sessão desconhecida ou tentativa de acessar outro usuário é rejeitada pelo servidor; a documentação explicita os limites dessa proteção simulada.
- [x] Há instruções reproduzíveis de instalação, execução e testes, incluindo como alcançar o servidor a partir do n8n e como isolar dados, credenciais e ações externas.
- [x] O contrato e as diferenças conhecidas em relação a uma integração real estão documentados para orientar o T-008.

## Test budget: 3 new test cases (ceiling, not a target)

- Caso 1: Sessão fictícia com análise de solo ausente: Flora consulta MCP e orienta a etapa anterior, identificando a simulação.
- Caso 2: Sessão fictícia com erro de validação: Flora indica o campo retornado; se a consulta falhar, informa a indisponibilidade sem inventar diagnóstico.
- Caso 3: Sessão desconhecida ou identidade de outro usuário é rejeitada sem expor seus dados.

## Notes

- Nenhum acesso ao backend está disponível no planejamento; confirmação do comportamento real cabe ao T-008.
- Implementado na branch `feature/T-007-practium-mcp-server-diagnostico-ativo` (commits `7927896`, `ff3ce19`, `e6ab49b`), com push para `origin`. Detalhes em `practium-mcp-server/README.md`.
- Servidor MCP real em `practium-mcp-server/` (SDK MCP, transporte Streamable HTTP), com fixtures sintéticas, 3 testes automatizados passando e smoke script.
- Workflows n8n: `[T-007] assistente-suporte-tecnico (MCP simulado)` (`GU2dSb6BGJlGJQRT`, inativo); `[T-007] knowledgeBase simulada` (`PyjD9HpRTk3M3N2G`); `[T-007] Call Suporte (no-op)` (`tCZfdm7LCk2MkarX`). Nenhum workflow de produção foi alterado ou ativado.
- Evidências ponta a ponta no chat n8n: execuções `37681` (dependência ausente), `37677` (erro de validação), `37692` (perfil), falha simulada com `sim-session-degraded` sem diagnóstico inventado e `37686` (`Call Suporte` no-op, sem e-mail).
