# Módulo 03: Ingestão de Documentos, Contextual RAG e Segurança

**Arquivo Alvo:** `assistente-suporte-tecnico.json`  
**Áreas do Canvas:** `Download Files`, `Type File Router`, `Convert Documents to Markdown`, `Record Manager`, `Generate Chunk Description`, `Indexing in Vector DB`

---

## 1. Visão Geral do Módulo

Este módulo implementa o pipeline ETL (Extract, Transform, Load) da base de conhecimento do **Practium**:
1. Monitora criações, atualizações e exclusões de arquivos no Google Drive ou via Webhook (`POST /send-file`).
2. Converte múltiplos formatos (`TXT/MD`, `HTML`, `PDF/DOCX/XLS`) para Markdown estruturado usando OCR da Mistral (`mistral-ocr-latest`) com reconstrução de tabelas HTML in-line.
3. Gerencia idempotência via hash criptográfico na tabela `document_records_as` (Record Manager).
4. Divide o documento com `Recursive Markdown Text Splitter` customizado (`chunkSize = 1000`, `chunkOverlap = 0`).
5. Aplica **Contextual Retrieval** usando `gpt-4.1-mini` (`Generate Chunk Description`) antes de gerar embeddings (`Embeddings OpenAI`) e salvar na tabela `documents_as` do Supabase.

---

## 2. Estado Atual e Gargalos Identificados

1. **Subutilização da Chamada LLM no Contextual Retrieval (`Generate Chunk Description`):**
   - O nó já envia o documento inteiro (`<document>`) e o trecho (`<chunk>`) para o `gpt-4.1-mini`, mas solicita apenas um contexto genérico curto.
   - No domínio agrícola (Practium), produtores usam vocabulário coloquial (ex: *"jogar adubo"*, *"corrigir terra"*, *"lançar colheita"*) enquanto os manuais usam termos técnicos (*"recomendação de adubação"*, *"calagem"*, *"produtividade do talhão"*).
2. **Credenciais Expostas em Texto Claro (Segurança):**
   - No nó `Get Ocr Results` (linha 1254 do `assistente-suporte-tecnico.json`), o header `Authorization` contém uma chave real da API Mistral hardcoded (`Bearer lY8YW1...`), embora o nó já utilize a credencial `httpBearerAuth` (`Bearer Auth Mistral account`).
   - Nos nós `Uplod file to Mistral` e `Get Url Signed`, há headers `Authorization` vazios ou redundantes que podem conflitar com a injeção automática da credencial.

---

## 3. Arquitetura Alvo (Refatoração Imediata)

### 3.1. Enriquecimento Semântico no `Generate Chunk Description`
Atualizar o prompt do `gpt-4.1-mini` para gerar um cabeçalho contextual denso em português (sem alterar o número de chamadas à API), contendo:
1. **Contexto Situacional:** A qual manual/funcionalidade e seção do sistema Practium aquele trecho pertence.
2. **Categoria e Tela/Caminho:** Classificação implícita (`Navegação`, `Cadastro`, `Correção de Erro`, `Planos/Políticas`) e menção explícita a menus/telas citados.
3. **Sinônimos e Intenções do Usuário:** Termos práticos que um produtor de café ou consultor agrícola usaria ao buscar aquela informação.

### 3.2. Sanitização de Headers de Autenticação
- Remover os headers manuais `Authorization` nos nós `Uplod file to Mistral`, `Get Url Signed` e `Get Ocr Results`, delegando 100% para a credencial `httpBearerAuth` do n8n.

---

## 4. Evolução Futura (Structured Metadata Extraction)
- Alterar o `Generate Chunk Description` para retornar um JSON estruturado (`response_format: json_schema`) extraindo campos dedicados (`topic`, `screen_path`, `is_step_by_step`) para popular diretamente o objeto `metadata` no Supabase, permitindo reativar filtros exatos por `topic` na RPC `hybrid_search_as`.

---

## 5. Tickets Relacionados
- `tickets/T-003-ingestao-contextual-enriquecida-e-seguranca.md`
- `tickets/T-010-extracao-estruturada-metadados-na-ingestao.md`
