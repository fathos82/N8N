# Módulo 05: Engenharia de Prompt da Agente Flora e Orquestração de Tools

**Arquivo Alvo:** `assistente-suporte-tecnico.json`  
**Nó Principal:** `Flora` (`@n8n/n8n-nodes-langchain.agent`) e Tools conectadas (`knowledgeBase`, `Think`, `Call Suporte`)

---

## 1. Visão Geral do Módulo

A agente **Flora** (`gpt-4.1`) é o núcleo de atendimento ao cliente da plataforma **Practium**. Ela opera sob um Procedimento Operacional Padrão (POP) rigoroso para evitar alucinações, decompor múltiplas dúvidas em buscas independentes, guiar o usuário **uma etapa por vez** (Paced Delivery) e escalar para um atendente humano (`Call Suporte`) apenas quando as tentativas na base de conhecimento se esgotarem.

---

## 2. Estado Atual e Gargalos Identificados

1. **Desconexão entre o Prompt e o Retorno da `knowledgeBase`:**
   - O prompt instrui: *"Tente elaborar a URL a partir de metadata e da info da base de conhecimento"*, mas não explica a estrutura do `metadata` retornado pela tool.
   - O prompt não orienta como agir quando a busca retorna resultados de **confiança média** (`0.50 <= score < 0.75`) versus **confiança alta** (`>= 0.75`).
2. **Perda de Controle de Posição em Tutoriais Longos:**
   - Embora os exemplos *Few-Shot* mostrem a entrega etapa por etapa, o agente não numera explicitamente o progresso (`Passo 1 de N`), o que dificulta a ancoragem da conversa no histórico de memória.
3. **Ausência de Instruções para Entradas Multimodais:**
   - Com a chegada de transcrições de áudio e análises de prints de tela (Módulo 04), o prompt precisa instruir a Flora a usar os dados extraídos do print (nome da tela, mensagem de erro visualizada, campos vazios) diretamente nas queries enviadas para a `knowledgeBase`.

---

## 3. Arquitetura Alvo (Refatoração Imediata)

### 3.1. Atualização do System Prompt da `Flora`
1. **Interpretação de Insumos Multimodais:**
   - Reconhecer blocos `[Mensagem de áudio transcrita]` e `[Análise da Imagem/Print enviado pelo usuário]`.
   - Usar imediatamente o texto do erro ou o nome da tela identificados no print para consultar a `knowledgeBase`, sem perguntar novamente ao usuário o que já está visível na imagem.
2. **Protocolo de Confiança da Busca (`ALTA` vs `MEDIA`):**
   - **Confiança `ALTA` (`>= 0.75`):** Iniciar imediatamente a entrega passo a passo.
   - **Confiança `MEDIA` (`0.50` a `0.74`):** Confirmar brevemente com o usuário se a dúvida se refere àquele procedimento encontrado antes de ditar todas as etapas, evitando guiar o usuário pelo fluxo errado.
   - **Sem resultados (`hasResults: false`):** Fazer até 1 nova tentativa na `knowledgeBase` reformulando os termos (sinônimos mais amplos) antes de pedir mais detalhes ou acionar `Call Suporte`.
3. **Ancoragem Explícita de Etapas (`Passo X de Y`):**
   - Sempre indicar em qual etapa do procedimento o usuário está (ex: *"Passo 1 de 4: ..."*), facilitando o rastreamento na memória do Postgres.
4. **Construção de Links / URLs com `base_url` e `metadata`:**
   - Utilizar `base_url` (`practium-client.utheuz.com`) combinada apenas com rotas/caminhos explicitamente presentes no texto ou `metadata` do documento (proibindo adivinhar rotas inexistentes).

---

## 4. Tickets Relacionados
- `tickets/T-005-refinamento-prompt-flora-e-uso-de-metadados.md`
- `tickets/T-006-corrective-rag-e-multi-query-expansion.md`
