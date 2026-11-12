# T-008: Integrar diagnóstico MCP ao backend real do Practium

**Status:** blocked
**Depends on:** T-007
**Owner:** -

## Goal

Evoluir a simulação do T-007 para diagnóstico somente de leitura com dados reais autorizados do Practium, preservando o contrato MCP quando possível e adaptando-o às interfaces e regras efetivamente disponíveis.

## Scope

- Referência: `arquiteture/06-practium-mcp-and-code-migration.md` e contrato implementado no T-007.
- Com acesso autorizado, levantar API, documentação, ambiente de homologação, modelos de dados, logs, limites e credenciais; validar a cadeia de dependências e quais dados estão de fato disponíveis. Preferir API oficial; acesso direto ao banco requer autorização explícita.
- Implementar adaptador de leitura para as três tools do T-007, documentar divergências do contrato e preservar modo simulado isolado para testes.
- Integrar identidade autenticada e autorização por usuário/tenant no servidor a partir de contexto confiável; não confiar em IDs fornecidos pelo modelo ou front-end sem validação. Documentar gestão de segredos, minimização de dados, logs sem dados sensíveis e falha fechada.
- Validar em homologação a integração da Flora, tratamento de indisponibilidade, dados ausentes e erros de permissão; definir procedimento seguro de configuração e implantação, sem ativação em produção automática.

## Out of scope

- Escrita ou alteração de dados Practium e acesso irrestrito a dados de outros usuários.
- Assumir schemas, permissões ou existência de logs não confirmados; liberação para produção sem autorização.

## Acceptance criteria

- [ ] Interfaces, permissões e ambientes reais são confirmados e as diferenças em relação à simulação documentadas.
- [ ] As três tools retornam dados reais autorizados em homologação, ou uma limitação comprovada é tratada e comunicada sem inventar dados.
- [ ] Identidade e tenant são verificados no servidor; acesso cruzado e contexto não autenticado são negados, inclusive em falhas do backend.
- [ ] Flora usa os resultados reais disponíveis e informa indisponibilidade ou ausência de dados sem apresentar fixtures como dados reais.
- [ ] Configuração, segredos, testes de homologação, limitações e procedimento de implantação estão documentados; simulação e backend real permanecem explicitamente separados.

## Test budget: 3 new test cases (ceiling, not a target)

- Caso 1: Usuário autorizado com dependência ausente recebe diagnóstico baseado no backend de homologação.
- Caso 2: Erro de validação disponível é consultado; indisponibilidade ou ausência é comunicada sem diagnóstico inventado.
- Caso 3: Identidade ausente ou acesso a outro usuário/tenant é negado sem vazamento de dados.

## Notes

- Bloqueado: acesso ao backend, documentação das interfaces e credenciais de homologação ainda não estão disponíveis. Próximo passo: obter acesso autorizado e concluir T-007 antes de iniciar.
