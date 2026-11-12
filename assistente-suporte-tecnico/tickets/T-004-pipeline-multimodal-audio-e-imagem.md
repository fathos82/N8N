# T-004: Implementar pipeline multimodal de entrada para Áudio (Whisper) e Imagem (Vision)

**Status:** done
**Depends on:** T-002
**Owner:** implementor

## Goal

Permitir que o usuário envie áudios e capturas de tela (prints de erros ou telas da plataforma Practium) no chat, transcrevendo áudios via OpenAI Whisper e extraindo diagnóstico visual estruturado via `gpt-4.1-mini` Vision antes de acionar a agente Flora.

## Scope

- Referência arquitetural: `arquiteture/04-multimodal-input-pipeline.md`
- Arquivo `assistente-suporte-tecnico.json`:
  - Nó `When chat message received` (ativação de `allowFileUploads: true` e `allowedFilesMimeTypes: "image/*,audio/*"`)
  - Preservação do payload binário (`$binary`) durante a verificação de status da sessão ou referência direta ao binário do trigger
  - Criação do nó roteador `Media Router` (`Switch`) após `Extract Query` verificando presença e `mimeType` de arquivos enviados
  - Criação do nó `Transcribe Audio` (OpenAI Whisper) e formatação de saída para `chatInput`
  - Criação do nó `Analyze Screen Image` (OpenAI Vision `gpt-4.1-mini`) com prompt de diagnóstico de telas/erros do Practium e concatenação ao `chatInput`

## Out of scope

- Processamento de arquivos de documentos complexos (PDF, XLSX) enviados pelo chat do cliente final (o chat aceita imagens e áudios)
- Criação de novas credenciais externas (deve reutilizar a credencial `OpenAi account` existente `0LtvSfR1BUp6aWpc`)

## Acceptance criteria

- [x] O nó `When chat message received` possui `allowFileUploads: true` habilitado para `image/*,audio/*`.
- [x] Mensagens contendo apenas texto seguem diretamente para o nó `Flora` sem chamadas extras de API.
- [x] Mensagens contendo áudio (`audio/*`) são transcritas pelo nó OpenAI Audio e entregues à `Flora` no campo `chatInput`.
- [x] Mensagens contendo imagem (`image/*`) são analisadas pelo nó OpenAI Vision (`gpt-4.1-mini`), que extrai a tela, mensagens de erro e campos visíveis e os anexa ao `chatInput` recebido pela `Flora`.

## Test budget: 3 new test cases (ceiling, not a target)

- Caso 1: Envio de print de tela com erro de validação passa pela rota `IMAGE` e entrega à Flora a descrição da tela e o texto exato do erro — positivo
- Caso 2: Envio de mensagem de voz passa pela rota `AUDIO` e entrega à Flora o texto transcrito em português — positivo
- Caso 3: Envio de mensagem de texto puro sem anexo binário passa pela rota `TEXT_ONLY` sem acionar Whisper ou Vision — negativo proposital

## Notes

- Implementado na branch `feature/T-004-pipeline-multimodal-audio-e-imagem`, commit `c7602bf9f7b9044001e1cadcecabc43b09325943`, com push confirmado em `origin`.
- Validação estática: JSON parseável, 98 nós, 78 conexões, IDs únicos, `git diff --check` aprovado e diff limitado ao workflow alvo.
- Validação MCP dos 8 nós relevantes: todos válidos, 0 erros e 0 warnings; validação completa retornou `valid: true`, com warnings pré-existentes fora do escopo.
- Rotas verificadas: `AUDIO` → `Transcribe Audio` → `Format Audio for Flora`; `IMAGE` → `Analyze Screen Image` → `Format Image for Flora`; `TEXT_ONLY` → `Flora`.
- Simulações estáticas dos três casos de aceite passaram, incluindo fallback para `TEXT_ONLY` e restauração do binário.
- O runtime live não foi executado porque a cópia remota ainda está na versão anterior e uma execução real acionaria Postgres/OpenAI; a limitação é de evidência runtime, não de validação estática.
- `Settings1` não existe no workflow alvo; nenhum arquivo fora do escopo foi alterado.
