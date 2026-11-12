# Módulo 06: Practium MCP Server e Evolução Code-First (Futuro / Avançado)

**Status Arquitetural:** Planejamento de Médio/Longo Prazo (Fase 2)  
**Escopo:** Integração ativa com o ecossistema **Practium** via MCP (Model Context Protocol) e desacoplamento do runtime agêntico.

---

## 1. Visão Geral do Módulo

Atualmente, a agente **Flora** atua apenas de forma **passiva/documental**: ela lê manuais estáticos para tentar adivinhar por que o usuário está enfrentando um problema na plataforma Practium.

Este módulo planeja o suporte ativo via **MCP (Model Context Protocol)** em duas etapas: primeiro uma simulação local com dados fictícios (T-007), depois a conexão autorizada ao Practium real (T-008). Também prepara uma possível arquitetura **Code-First**.

---

## 2. Servidor MCP do Practium (`practium-support-mcp`)

MCP é um protocolo pelo qual um cliente descobre e chama ferramentas expostas por um servidor, com entradas e respostas estruturadas. Aqui, a Flora usa o cliente MCP do n8n; o servidor expõe ferramentas de diagnóstico de leitura. Na primeira fase, um adaptador devolve fixtures fictícias; na segunda, um adaptador acessa interfaces reais autorizadas. Uma API HTTP genérica, por si só, não é um servidor MCP.

### 2.1. Ferramentas (Tools) do MCP
1. `get_user_context`
   - Retorna: Nome do usuário, `role` exato no sistema, plano contratado (`free`, `profissional`, `business`), e permissões ativas.
2. `check_onboarding_dependencies`
   - Verifica a cadeia de pré-requisitos de cadastro no Practium:
     - Possui Propriedade/Fazenda cadastrada?
     - Possui Talhão cadastrado na Fazenda?
     - Possui Análise de Solo vinculada ao Talhão?
     - Possui Recomendação de Adubação gerada?
   - A cadeia é uma hipótese de teste e deverá ser confirmada com o backend real; não se deve presumir frequência ou tempo de diagnóstico.
3. `get_recent_validation_errors` (janela opcional, sujeita ao contrato implementado)
   - Consulta os logs recentes de API/Front-end do usuário para identificar exatamente qual validação falhou (ex: `Campo 'Fósforo (P)' deve ser numérico positivo na tela /analise-solo/novo`).

---

## 3. Arquitetura Híbrida vs. Code-First

### Fase 2A: Simulação MCP dentro do n8n (T-007)
- Utilizar um servidor MCP local e o nó `MCP Client Tool` nativo do n8n, em cópia isolada da Flora. Verificar o transporte suportado pela versão instalada (SSE ou Streamable HTTP) e a conectividade do n8n até o servidor; `localhost` dentro de um container não é necessariamente o host.
- Versionar fixtures sintéticas e documentar schemas, erros e reprodução ponta a ponta. O agente deve deixar claro que os resultados são simulados e não inventar diagnósticos quando as tools falharem. Desabilitar ou substituir ações externas como `Call Suporte` no ambiente de teste.
- A identidade simulada deve ser vinculada à sessão por configuração controlada pelo servidor; um ID fornecido pela agente não concede acesso a outro usuário. Esta verificação é apenas um modelo de teste, não autenticação real.

### Fase 2A.1: Backend real (T-008, bloqueado)
- Confirmar as APIs, os dados efetivamente disponíveis e o contrato após obter acesso autorizado e ambiente de homologação; não pressupor que as fixtures reflitam o backend.
- Substituir o adaptador fictício por leitura autorizada, mantendo modos explicitamente separados. Validar identidade e tenant com contexto confiável no servidor, falhar fechado e proteger segredos e dados sensíveis. Sem acesso ou identidade verificável, não habilitar dados reais.

### Fase 2B: Migração do Cérebro do Agente para Código (LangGraph / Mastra / Agent SDK)
- **O que permanece no n8n:** Gatilhos do Google Drive, OCR da Mistral, Webhooks de entrada/saída e notificações de e-mail (`Call Suporte`).
- **O que migra para código versionado (TypeScript/Python):**
  - Grafo determinístico de atendimento (Roteador de Intenção -> Diagnóstico MCP -> Busca Híbrida -> Entrega Passo a Passo com Checkpointer de Estado -> Verificador Anti-Alucinação).
  - Suíte de avaliação automatizada (Evals) com casos reais de dúvidas de produtores de café para testar regressão a cada mudança de prompt ou modelo.

---

## 4. Tickets Relacionados
- `tickets/T-007-practium-mcp-server-diagnostico-ativo.md`
- `tickets/T-008-integracao-practium-mcp-backend-real.md`
- `tickets/T-012-migracao-agente-code-first-langgraph-mcp.md` (pode avançar com simulação; integração real permanece no T-008)
