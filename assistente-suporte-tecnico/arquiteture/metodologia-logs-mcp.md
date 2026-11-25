# Metodologia de consulta aos logs (MongoDB MCP)

> Documento de trabalho. Base para o prompt do agente de suporte técnico do Practium.
> Escopo atual: **apenas a collection `logs`**. `activityhistories` fica para a próxima etapa.
> Levantamento feito em 25/11/2026 no ambiente **dev** (5.408 logs, 31/10 a 25/11/2026).

---

## 1. Pré-requisitos

### 1.1 Índices (criar antes de ativar o agente)

```js
db.logs.createIndex({ author: 1, createdAt: -1 })    // filtro principal: logs do usuário por data
db.logs.createIndex({ status: 1, createdAt: -1 })    // complemento: erros 5xx do system
db.logs.createIndex({ logType: 1, createdAt: -1 })   // eventos de negócio por tipo
```

Sem eles, todas as consultas fazem COLLSCAN e o `--indexCheck` do MCP bloqueia os `find` filtrados.

### 1.2 Observações sobre o MCP

- A tool `collection-indexes` falha fora do Atlas porque chama `$listSearchIndexes`. Para listar índices, use `aggregate` com `[{ $indexStats: {} }, { $project: { name: 1, key: 1 } }]`.
- O agente deve usar **sempre `aggregate`**, nunca `find`, porque só ele permite a projeção que remove dados pessoais (seção 6).

---

## 2. Anatomia de um log

| Campo | Tipo | Uso |
|---|---|---|
| `author` | string | `_id` do usuário (24 hex) **ou** `"system"` (requisição sem usuário identificado) |
| `logType` | string | `system_event` = resposta HTTP de erro; demais = evento de negócio (seção 5) |
| `status` | string | `Info` / `Warn` / `Error` |
| `httpStatus` | number \| null | Só em `system_event` |
| `log` | string | Texto livre. Contém **perfil + e-mail** do autor, método, rota e mensagem |
| `stackTrace` | string \| null | Stack interno do Node. **Nunca** trazer |
| `browser` | string | User-agent. Não trazer, salvo diagnóstico de navegador |
| `createdAt` | Date | Ordenação e janela |

Formatos do `log`:

- HTTP: `<Perfil> <email> gerou uma resposta HTTP <code> em <MÉTODO> <rota>: <mensagem>`
- Sem usuário: `Sistema gerou uma resposta HTTP <code> em <MÉTODO> <rota>: <mensagem>`
- Negócio: `<Perfil|id> <email> <verbo> <entidade> <nome>.` (ex.: "criou a análise de solo …")
- OCR: `OCR do job <uuid> finalizado com sucesso.`

---

## 3. Filtro de ruído (sempre aplicado, salvo queixa de acesso)

Cerca de 50% da collection é sessão expirada ou refresh inválido:

```js
$nor: [
  { httpStatus: 401, log: { $regex: "não está logado" } },
  { httpStatus: 406, log: { $regex: "Refresh-Token" } }
]
```

**Exceção:** se a queixa for de acesso ("não consigo entrar", "me desloga", "pede login toda hora"), **não** aplicar o filtro, e somar a rota `/login` (seção 5).

---

## 4. Funil de consulta

O agente para no primeiro passo que trouxer evidência suficiente.

| Passo | Filtro | Janela | Limite |
|---|---|---|---|
| **1. Por assunto** | `author = userId` + ruído + filtro de assunto (rota / logType / status) | 72h | 20 |
| **2. Sem o assunto** | `author = userId` + ruído | 72h | 10 |
| **3. Janela ampliada** | passo 1 (ou 2, se o assunto não estiver claro) | 7 dias | 20 |

Se os três passos vierem vazios, o agente responde que não encontrou registros e segue a seção 8.

Regras gerais:

- Sempre `$sort: { createdAt: -1 }` e `$limit` **antes** do `$project`.
- Se o usuário citar data ou horário ("ontem à tarde"), a janela passa a ser a citada, com margem de ±2h.
- No máximo **4 consultas** por atendimento.

### 4.1 Complemento: falhas gerais (`author: "system"`)

Os logs do `system` **não** podem ser atribuídos a um usuário. Eles servem apenas para:

- **Instabilidade geral:** `status: "Error"` (5xx) na mesma janela e na mesma rota/módulo do assunto, limite 5. Se aparecer, o problema provavelmente não é do usuário.
- **Login:** `POST /login` com 401 apenas confirma que houve tentativas falhas no período, sem saber de quem. Não usar como prova sobre o usuário.

Nunca trazer logs do `system` sem filtro de status ou rota.

---

## 5. Tabela de assuntos → filtros

> Fontes: collection do Postman "practium 2.0" (266 requisições) + rotas observadas nos logs de dev em 25/11/2026.
> Rotas marcadas com † aparecem nos logs mas **não** na collection (a collection está desatualizada em relação à API).
> No `$match`, o filtro de rota é um `$regex` sobre `log`, sempre começando com espaço para pegar só a rota: `{ log: { $regex: " /soil-analysis/" } }`.
> Quando o assunto tem rota **e** logType, usar `$or: [{ log: { $regex: ... } }, { logType: { $in: [...] } }]`.

### 5.1 Cadastros da fazenda

| Assunto (como o usuário fala) | Regex de rota (em `log`) | logTypes | Ações cobertas |
|---|---|---|---|
| **Propriedade / fazenda** | ` /user/prop/(create\|update\|delete\|get\|duplicate\|updateAvatar\|deleteAvatar)\| /prop/` | `property_created` | cadastrar, editar, excluir, duplicar, foto, listar fazendas |
| **Áreas** | ` /user/prop/[^/ ]+/area/(create\|delete)\| /user/prop/area/` | `area_created`, `area_updated` | cadastrar, excluir, listar áreas |
| **Setores / talhões** | ` /sector/` | `sector_created`, `sector_updated`, `sector_duplicated` | cadastrar, editar, excluir, duplicar, foto |
| **Vínculo consultor ↔ agricultor / clientes** | ` /binding-users?/\| /prop/findAllByBoundUsers` | `binding_user_created`, `binding_user_deleted` | convidar ou vincular consultor, editar, remover vínculo |

### 5.2 Análises

| Assunto | Regex de rota | logTypes | Ações cobertas |
|---|---|---|---|
| **Análise de solo** | ` /soil-analysis/` | `soil_analysis_created`, `soil_analysis_updated`, `soil_analysis_deleted` | cadastrar (`store`), editar, excluir, laudo/interpretação (`appraisal`), relatório |
| **Análise foliar** | ` /plant-analysis/` | `plant_analysis_created`, `plant_analysis_updated`, `plant_analysis_deleted` | idem análise de solo |
| **Leitura automática de laudo (OCR)** | ` /ocr/` | `ocr_requested`, `ocr_finished`, `ocr_failed` | enviar PDF/foto do laudo (`extract/soil`, `extract/foliar`), acompanhar leitura (`verifyJob`) |

### 5.3 Recomendações

| Assunto | Regex de rota | logTypes | Ações cobertas |
|---|---|---|---|
| **Recomendação de plantio / correção (calagem, gessagem, adubação de plantio)** | ` /advices/planting/` | `planting_advice_created`, `planting_advice_updated`, `planting_advice_deleted` | iniciar, calcular calagem/gessagem/adubação, salvar, relatório, excluir |
| **Plano de adubação / fertilização** | ` /advices/fertilization-plan/` | `fertilization_plan_advice_created`, `fertilization_plan_advice_deleted` | criar, planejar, fracionar adubação, fases do ciclo†, prévia de demanda†, relatório, excluir |
| **Mistura / concentração de calda** | ` /advices/fertilization-plan/mixtures/`† | — | criar, editar mistura, calcular concentração |
| **Parcelamento** | ` /advices/parcelling/` | `parcelling_advice_created`, `parcelling_advice_updated`, `parcelling_advice_deleted` | criar (fixo† ou dinâmico†), editar, duplicar, excluir, listar |
| **Aplicação foliar** | ` /advices/foliar-application/` | `foliar_application_advice_created` | criar, editar, laudo, relatório, excluir |
| **Pacotes de fertilizantes** | ` /advices/fertilizer-pack/` | — | criar, editar, duplicar, excluir |
| **Tabela nutricional** | ` /advices/nutrition-table/` | — | consultar |

### 5.4 Catálogos e referências

| Assunto | Regex de rota | logTypes | Ações cobertas |
|---|---|---|---|
| **Fertilizantes (produtos)** | ` /products/fertilizer/` | — | cadastrar, editar, importar, fotos, excluir |
| **Defensivos agrícolas** | ` /agricultural-defensives/` | `agricultural_defensive_updated` | cadastrar, editar, importar, fotos, excluir, consultar |
| **Princípios ativos** | ` /active-ingredients/` | — | idem |
| **Pragas** | ` /pests/` | — | idem |
| **Culturas** | ` /cultures/` | — | idem |
| **Fabricantes** | ` /manufacturer/` | — | idem, inclusive "mais populares"† |
| **Solicitação de produto** (pedir inclusão de um produto no catálogo) | ` /request-products/` | `request_product_updated` | solicitar, acompanhar status |
| **Referências estaduais** | ` /state-reference/` | `state_reference_created`, `state_reference_updated`, `state_reference_deleted` | cadastrar, editar, excluir |
| **Referências do plano de adubação** | ` /fertilization-plan-reference/` | `fertilization_plan_reference_created`, `fertilization_plan_reference_updated` | cadastrar, editar, ativar, excluir |

### 5.5 Conta, acesso e assinatura

| Assunto | Regex de rota | logTypes | Ações cobertas |
|---|---|---|---|
| **Login / acesso / sessão** *(desligar o filtro de ruído)* | ` /(login\|logout\|refresh\|isauth\|auth/)` | `login`, `logout` | entrar, sair, login com Google, sessão expirada |
| **Cadastro / recuperação de senha** | ` /user/(register\|recover)` | `register` | criar conta, esqueci a senha |
| **Perfil** | ` /user/(get\|updateProfile\|profile/\|getThemePreference)` | `user_profile_updated` | editar dados, foto e capa, tema |
| **Termos, privacidade e consentimento** | ` /(consent\|policies\|policy-version)/` | — | aceitar termos, status do consentimento |
| **Exportar ou excluir meus dados (LGPD)** | ` /(user/data-export\|user-data-exports\|user/delete\|user/anonymize)` | — | pedir exportação, baixar, excluir conta. **Sempre escalar** |
| **Assinatura / plano** | ` /(user/plan/\|plan/\|landing/plan/)` | `checkout_started`, `plan_updated` | ver planos, assinar, upgrade, cancelar, reembolso, resumo† e cobranças† |
| **Pagamento** | ` /(payments\|gateway)/` | `payment_created`, `payment_updated` | pagamentos e cobrança. **Escalar se houver erro** |
| **Personalização de relatórios (logo)** | ` /report-settings/` | — | enviar ou remover logo dos relatórios |
| **Bot de WhatsApp** | ` /(bot/\|user/updateBotWhatsappConfig)` | — | configurar o bot |

### 5.6 Outros

| Assunto | Regex de rota | logTypes | Ações cobertas |
|---|---|---|---|
| **Dashboard / painel inicial** | ` /dashboard\| /advices/stats\| /soil-analysis/stats\| /prop/stats` | — | indicadores do painel |
| **Diário de campo / tarefas** | ` /field-diary/`† | — | lançamentos, tarefas, clientes |
| **Faturamento (consultor/gestor)** | ` /invoicing/`† | — | painel, fluxo de caixa, assinaturas vencendo |
| **Assistente Flora** | ` /flora/` | `flora_context_accessed` | contexto de análises usado pela Flora |
| **Chamados de suporte** | ` /support-tickets/` | `support_ticket_created` | abrir chamado, mensagens, status |
| **Busca de CEP** (cadastro de endereço) | ` /viacep/` | — | preenchimento automático do endereço |

### 5.7 Fora do escopo do agente

Rotas administrativas ou de integração que não interessam ao usuário final e **não devem ser consultadas**:
`/management/`, `/hierarchy/`, `/data-reports/`, `/webhook/`, `/api-docs`, `/testimonial`, `/contact-form`, `/user/online`†, `/user/countByStates`†, `/_bulk`†.

---

## 6. Tabela de tipo de queixa → status

Use junto com a tabela de assuntos. O status define **que tipo** de problema foi; o assunto define **onde**.

| Queixa típica | Filtro | Leitura para o usuário |
|---|---|---|
| "Dá erro ao salvar", "não aceita os dados" | `httpStatus: 400` | Algum dado do formulário não passou na validação; a mensagem do log diz qual |
| "Não tenho acesso", "não aparece a fazenda do cliente" | `httpStatus: 403` | Falta permissão ou vínculo (comum com consultor acessando propriedade de terceiros) |
| "Sumiu", "não encontra" | `httpStatus: 404` | O registro não existe mais ou nunca foi criado; conferir logTypes `*_deleted` |
| "Diz que já existe", "não deixa criar" | `httpStatus: 409` | Registro duplicado ou conflito de estado |
| "Travou", "erro inesperado", "tente mais tarde" | `status: "Error"` (5xx) | Falha da plataforma, não do usuário → **escalar** (seção 8) |
| "Enviei o laudo e não leu" | `logType: "ocr_failed"` | A leitura automática falhou; sugerir reenvio ou cadastro manual |
| "Salvei mas não sei se foi", "fiz e sumiu" | logTypes `*_created` / `*_updated` / `*_deleted` | Confirma se a ação aconteceu e quando |
| Queixa vaga | sem filtro de status | Passo 2 do funil |

---

## 7. Pipeline modelo

A projeção remove o prefixo `<Perfil> <email>` do texto e nunca traz `stackTrace`, `browser` nem `author`.

```js
[
  { $match: {
      author: "<USER_ID>",
      createdAt: { $gte: ISODate("<AGORA - 72h>") },
      $nor: [
        { httpStatus: 401, log: { $regex: "não está logado" } },
        { httpStatus: 406, log: { $regex: "Refresh-Token" } }
      ],
      // filtro de assunto (opcional), ex.:
      $or: [
        { log: { $regex: " /soil-analysis/" } },
        { logType: { $in: ["soil_analysis_created", "soil_analysis_updated", "soil_analysis_deleted"] } }
      ]
  }},
  { $sort: { createdAt: -1 } },
  { $limit: 20 },
  { $project: {
      _id: 0,
      quando: "$createdAt",
      tipo: "$logType",
      status: 1,
      httpStatus: 1,
      requisicao: { $let: {
        vars: { r: { $regexFind: { input: "$log", regex: "(GET|POST|PUT|PATCH|DELETE) [^ :?]+" } } },
        in: "$$r.match"
      }},
      texto: { $ifNull: [
        { $let: {
            vars: { r: { $regexFind: { input: "$log", regex: "> (.*)$" } } },
            in: { $arrayElemAt: ["$$r.captures", 0] }
        }},
        "$log"
      ]}
  }}
]
```

✅ Validado no MCP em 25/11/2026. Exemplo de saída (sem dados pessoais):

```json
{ "quando": "2026-11-25T13:52:44Z", "tipo": "system_event", "status": "Warn", "httpStatus": 409,
  "requisicao": "POST /soil-analysis/store",
  "texto": "gerou uma resposta HTTP 409 em POST /soil-analysis/store: Não foi possível enquadrar Pm1 usando Prem, argila ou textura da análise de solo." }
```

Note que as mensagens de 400/409 da API já são explicativas e servem de base para a explicação ao usuário.

Campo `texto`:

- Logs de usuário: tudo depois de `> ` ("gerou uma resposta HTTP 400 em POST …: <mensagem>" ou "criou a análise de solo …").
- Logs do `system`: o texto inteiro, que não tem e-mail.

---

## 8. Dados sensíveis e linguagem

**Nunca mostrar ao usuário**, mesmo que venha na consulta:

- e-mail, nome de outras pessoas, `_id`s, `author`, UUIDs de job
- `stackTrace`, caminhos de arquivo (`/app/dist/...`), nomes de middleware
- rotas, métodos HTTP e códigos de status crus
- user-agent

Traduzir para linguagem simples:

- "Ontem às 14h, ao salvar a análise de solo, a plataforma recusou porque…"
- Nunca: "POST /soil-analysis/store retornou 409".

---

## 9. Quando escalar para um humano

- Qualquer `status: "Error"` (5xx) relacionado ao assunto.
- 5xx repetido do `system` na mesma rota (instabilidade geral).
- Erro de permissão (403) que o usuário diz não fazer sentido.
- Funil vazio, mas o usuário insiste que o problema aconteceu.
- Pagamento ou cobrança com qualquer erro.

Ao escalar, o agente registra um resumo técnico interno (rota, status, horário) **separado** da resposta ao usuário.

---

## 10. Pendências

- [ ] Revisar com o time as rotas marcadas com † (presentes nos logs, ausentes na collection do Postman).
- [ ] Testar no MCP os regex de cada assunto da seção 5 (contagem por assunto).
- [ ] Criar os índices da seção 1.1 (dev e prod).
- [ ] Revisar a role `mcpLeitura`: hoje permite ler `users` (fora do escopo "só logs").
- [ ] Médio prazo (backend): gravar `method`, `route`, `userId` e `propId` como campos estruturados no log e tirar o e-mail do texto livre.
- [ ] Próxima etapa: `activityhistories` (ações feitas por consultor em nome do agricultor, via `actorUserId`).
