# Módulo 04: Pipeline Multimodal de Entrada (Áudio e Imagem)

**Arquivo Alvo:** `assistente-suporte-tecnico.json`  
**Área do Canvas:** Entre a verificação de sessão (`Extract Query`) e o Agente (`Flora`)

---

## 1. Visão Geral do Módulo

Usuários de sistemas agrícolas frequentemente têm dificuldade em descrever mensagens de erro por texto ou preferem enviar **áudios** e **capturas de tela (prints)** da plataforma **Practium**. Este módulo adiciona capacidade multimodal nativa na entrada do chat, convertendo áudios e imagens em contexto técnico estruturado antes de acionar a agente **Flora**.

---

## 2. Estado Atual

Atualmente, o nó `When chat message received` não habilita o upload de arquivos (`allowFileUploads` ausente) e o nó `Extract Query` repassa exclusivamente `chatInput` (string de texto) para a `Flora`. Qualquer anexo enviado é ignorado.

---

## 3. Arquitetura Alvo (Implementação Imediata)

### 3.1. Habilitação no Trigger (`When chat message received`)
Configurar em `options`:
- `allowFileUploads: true`
- `allowedFilesMimeTypes: "image/*,audio/*"`

### 3.2. Preservação de Binários e Roteamento (`Media Router`)
Logo após a validação de status da conversa (no ponto do `Extract Query`), um nó `Switch` (`Media Router`) inspeciona se há arquivos binários anexados na mensagem do usuário:

1. **Rota `AUDIO` (`mimeType` começa com `audio/`):**
   - Aciona o nó nativo da OpenAI (`resource: "audio"`, `operation: "transcribe"`, modelo `whisper-1`) usando a credencial `OpenAi account` (`id: 0LtvSfR1BUp6aWpc`) já existente no workflow.
   - Formata o `chatInput` combinando o texto eventual digitado pelo usuário com a transcrição:
     `[Mensagem de áudio transcrita]: {{ $json.text }}`

2. **Rota `IMAGE` (`mimeType` começa com `image/`):**
   - Aciona o nó nativo da OpenAI (`resource: "image"`, `operation: "analyze"`, modelo `gpt-4.1-mini`) usando a mesma credencial `OpenAi account`.
   - Prompt de Visão especializado no Practium:
     > *"Você é um especialista em diagnóstico visual da plataforma agrícola Practium. Analise a imagem enviada pelo usuário e descreva de forma estruturada em português: 1) Qual tela, menu ou formulário do sistema aparece na imagem; 2) Qualquer mensagem de erro, alerta, modal ou campo destacado com erro; 3) Quais campos estão visíveis (preenchidos ou vazios) que ajudem a entender a dúvida ou o problema do usuário."*
   - Formata o `chatInput` combinando a mensagem do usuário com o laudo visual da imagem:
     `Mensagem do usuário: {{ chatInput }}\n\n[Análise da Imagem/Print enviado pelo usuário]:\n{{ analise_visao }}`

3. **Rota `TEXT_ONLY` (Sem binário ou fallback):**
   - Segue diretamente com o `chatInput` original para o agente `Flora`.

---

## 4. Benefícios Diretos
- **Zero configuração de novas credenciais:** Reutiliza a credencial `OpenAi account` já ativa no n8n.
- **Identificação imediata de erros:** Quando o usuário envia um print de erro ao salvar uma análise de solo, a Flora já recebe o texto exato do erro e os campos da tela, pulando a etapa de perguntar ao usuário *"qual é a mensagem de erro?"* e indo direto à busca da solução na `knowledgeBase`.

---

## 5. Tickets Relacionados
- `tickets/T-004-pipeline-multimodal-audio-e-imagem.md`
- `tickets/T-005-refinamento-prompt-flora-e-uso-de-metadados.md`
