import http from 'node:http';
import { randomUUID } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import { z } from 'zod';
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/streamableHttp.js';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const DEFAULT_FIXTURES = path.join(HERE, '..', 'fixtures', 'sessions.json');
const PORT = Number(process.env.PORT || 3907);
const HOST = process.env.HOST || '0.0.0.0';
const FIXTURES_PATH = process.env.MCP_FIXTURES_PATH || DEFAULT_FIXTURES;
const SESSION_TTL_MS = Number(process.env.MCP_SESSION_TTL_MS || 30 * 60 * 1000);
const CONTRACT_VERSION = 'T-007/0.1';
const DISCLAIMER =
  'Dados SIMULADOS a partir de fixtures sintéticas do T-007. Não são dados reais do Practium e esta proteção de identidade não é autenticação real.';

function loadFixtures() {
  const raw = JSON.parse(readFileSync(FIXTURES_PATH, 'utf8'));
  if (!raw.sessions || !raw.users) {
    throw new Error('Fixtures inválidas: esperado objetos "sessions" e "users".');
  }
  for (const [token, session] of Object.entries(raw.sessions)) {
    if (!session.user_id || !raw.users[session.user_id]) {
      throw new Error(`Sessão ${token} aponta para usuário inexistente.`);
    }
  }
  return raw;
}

const fixtures = loadFixtures();
const sessions = new Map(); // mcp-session-id -> { transport, server, token, lastSeen }

function sessionForToken(token) {
  const session = fixtures.sessions[token];
  if (!session) return null;
  return { token, ...session, user: fixtures.users[session.user_id] };
}

function jsonRpcError(res, status, code, message) {
  res.writeHead(status, { 'content-type': 'application/json' });
  res.end(JSON.stringify({ jsonrpc: '2.0', error: { code, message }, id: null }));
}

function toolError(code, message, extra = {}) {
  return {
    isError: true,
    content: [
      {
        type: 'text',
        text: JSON.stringify(
          {
            simulated: true,
            error: { code, message, ...extra },
            disclaimer: DISCLAIMER,
          },
          null,
          2,
        ),
      },
    ],
  };
}

function toolOk(payload) {
  return {
    content: [
      {
        type: 'text',
        text: JSON.stringify(
          {
            ...payload,
            simulated: true,
            contract_version: CONTRACT_VERSION,
            data_source: 'fixtures/sessions.json',
            disclaimer: DISCLAIMER,
          },
          null,
          2,
        ),
      },
    ],
  };
}

function assertIdentity(session, requestedUserId) {
  if (requestedUserId && requestedUserId !== session.user_id) {
    return toolError(
      'IDENTITY_MISMATCH',
      'A identidade solicitada diverge da sessão MCP. Nenhum dado foi retornado.',
      { session_user_id: session.user_id, requested_user_id: requestedUserId },
    );
  }
  return null;
}

function unavailable(session) {
  if (!session.simulate_failure) return null;
  return toolError(
    'SIMULATED_BACKEND_UNAVAILABLE',
    'Indisponibilidade simulada: a consulta de fixtures falhou. Não há diagnóstico disponível e nenhum dado foi retornado.',
    { session_label: session.label },
  );
}

function createServer(session) {
  const server = new McpServer(
    { name: 'practium-support-mcp-sim', version: '0.1.0' },
    {
      instructions:
        'Servidor MCP de SIMULAÇÃO do diagnóstico ativo da Flora (Practium, T-007). ' +
        'Todas as respostas são fictícias e identificadas com simulated=true. ' +
        'A identidade é definida pelo token de sessão configurado no servidor; nunca informe user_id. ' +
        'Se uma tool falhar, não invente diagnóstico: informe indisponibilidade e ofereça escalonamento.',
    },
  );

  server.registerTool(
    'get_user_context',
    {
      title: 'Consultar contexto do usuário (simulado)',
      description:
        'Retorna perfil fictício do usuário vinculado à sessão MCP: nome, role exato, plano e permissões ativas. ' +
        'Somente leitura. Não aceita escolha de usuário; o campo user_id serve apenas para testar rejeição de identidade divergente.',
      inputSchema: {
        user_id: z
          .string()
          .optional()
          .describe('NÃO USE. Se informado e divergir da sessão, a chamada é rejeitada.'),
      },
    },
    async ({ user_id }) => {
      const mismatch = assertIdentity(session, user_id);
      if (mismatch) return mismatch;
      const failure = unavailable(session);
      if (failure) return failure;

      return toolOk({
        session_label: session.label,
        user: {
          user_id: session.user_id,
          display_name: session.user.display_name,
          role: session.user.role,
          role_label: session.user.role_label,
          plan: session.user.plan,
          active_permissions: session.user.active_permissions,
        },
      });
    },
  );

  server.registerTool(
    'check_onboarding_dependencies',
    {
      title: 'Verificar dependências de onboarding (simulado)',
      description:
        'Verifica a cadeia fictícia de pré-requisitos: propriedade/fazenda, talhão, análise de solo e recomendação de adubação. ' +
        'Retorna o status de cada etapa, o que está ausente/bloqueado e o próximo passo recomendado. Somente leitura.',
      inputSchema: {
        user_id: z
          .string()
          .optional()
          .describe('NÃO USE. Se informado e divergir da sessão, a chamada é rejeitada.'),
      },
    },
    async ({ user_id }) => {
      const mismatch = assertIdentity(session, user_id);
      if (mismatch) return mismatch;
      const failure = unavailable(session);
      if (failure) return failure;

      const chain = session.user.onboarding.map((step) => ({ ...step }));
      const missing = chain.filter((step) => step.status === 'missing');
      const blocked = chain.filter((step) => step.status === 'blocked');

      return toolOk({
        user_id: session.user_id,
        all_satisfied: missing.length === 0 && blocked.length === 0,
        chain,
        missing_steps: missing.map((step) => step.key),
        blocked_steps: blocked.map((step) => step.key),
        next_recommended_step:
          missing.length > 0
            ? {
                action: 'orientar_cadastro',
                target_step: missing[0].key,
                message: missing[0].guidance || missing[0].detail,
              }
            : blocked.length > 0
              ? {
                  action: 'resolver_dependencia',
                  target_step: blocked[0].depends_on || blocked[0].key,
                  message: blocked[0].detail,
                }
              : { action: 'nenhuma_acao', message: 'Cadeia fictícia completa.' },
      });
    },
  );

  server.registerTool(
    'get_recent_validation_errors',
    {
      title: 'Consultar erros de validação recentes (simulado)',
      description:
        'Retorna erros fictícios de validação de front-end/API dentro da janela informada. ' +
        'Se não houver erros, retorna lista vazia; não infere nem inventa diagnóstico. Somente leitura.',
      inputSchema: {
        window_minutes: z
          .number()
          .int()
          .min(1)
          .max(1440)
          .optional()
          .describe('Janela em minutos (1-1440). Padrão: 60.'),
        user_id: z
          .string()
          .optional()
          .describe('NÃO USE. Se informado e divergir da sessão, a chamada é rejeitada.'),
      },
    },
    async ({ window_minutes, user_id }) => {
      const mismatch = assertIdentity(session, user_id);
      if (mismatch) return mismatch;
      const failure = unavailable(session);
      if (failure) return failure;

      const windowMinutes = window_minutes ?? 60;
      const now = Date.now();
      const errors = session.user.validation_errors
        .filter((error) => error.occurred_minutes_ago <= windowMinutes)
        .map((error) => ({
          id: error.id,
          occurred_at: new Date(now - error.occurred_minutes_ago * 60_000).toISOString(),
          occurred_minutes_ago: error.occurred_minutes_ago,
          source: error.source,
          screen: error.screen,
          field: error.field,
          message: error.message,
          severity: error.severity,
        }));

      return toolOk({
        user_id: session.user_id,
        window_minutes: windowMinutes,
        count: errors.length,
        errors,
        note:
          errors.length === 0
            ? 'Nenhum erro fictício de validação na janela consultada. Não presuma a causa do problema.'
            : 'Erros fictícios retornados pelas fixtures; use apenas o campo/mensagem listados.',
      });
    },
  );

  return server;
}

async function readBody(req) {
  const chunks = [];
  let size = 0;
  for await (const chunk of req) {
    size += chunk.length;
    if (size > 1_000_000) throw new Error('Corpo da requisição excede 1 MB.');
    chunks.push(chunk);
  }
  if (chunks.length === 0) return undefined;
  const text = Buffer.concat(chunks).toString('utf8');
  if (!text.trim()) return undefined;
  return JSON.parse(text);
}

function tokenFromRequest(req, url) {
  const match = /^\/mcp\/([A-Za-z0-9_-]+)\/?$/.exec(url.pathname);
  if (match) return match[1];
  const auth = req.headers.authorization || '';
  const bearer = /^Bearer\s+([A-Za-z0-9_-]+)$/i.exec(auth);
  if (bearer) return bearer[1];
  return null;
}

async function handleMcp(req, res, url) {
  const token = tokenFromRequest(req, url);
  if (!token) {
    return jsonRpcError(res, 404, -32600, 'Endpoint MCP não encontrado. Use /mcp/<session-token>.');
  }

  const session = sessionForToken(token);
  if (!session) {
    return jsonRpcError(res, 401, -32001, 'Sessão desconhecida. Identidade não reconhecida pelo servidor.');
  }

  const headerSessionId = req.headers['mcp-session-id'];
  let entry = headerSessionId ? sessions.get(headerSessionId) : undefined;

  if (entry && entry.token !== token) {
    return jsonRpcError(
      res,
      403,
      -32003,
      'Identidade divergente: a sessão MCP pertence a outro token de sessão.',
    );
  }

  if (!entry) {
    if (req.method !== 'POST') {
      return jsonRpcError(res, 400, -32002, 'Sessão MCP ausente ou expirada.');
    }

    const server = createServer(session);
    const transport = new StreamableHTTPServerTransport({
      sessionIdGenerator: () => randomUUID(),
      enableJsonResponse: true,
      onsessioninitialized: (sessionId) => {
        sessions.set(sessionId, {
          transport,
          server,
          token,
          lastSeen: Date.now(),
        });
      },
    });
    transport.onclose = () => {
      if (transport.sessionId) sessions.delete(transport.sessionId);
    };
    await server.connect(transport);

    let body;
    try {
      body = await readBody(req);
    } catch (error) {
      return jsonRpcError(res, 400, -32700, `JSON inválido: ${error.message}`);
    }
    await transport.handleRequest(req, res, body);
    return;
  }

  entry.lastSeen = Date.now();
  let body;
  try {
    body = req.method === 'POST' ? await readBody(req) : undefined;
  } catch (error) {
    return jsonRpcError(res, 400, -32700, `JSON inválido: ${error.message}`);
  }
  await entry.transport.handleRequest(req, res, body);
}

const httpServer = http.createServer(async (req, res) => {
  const url = new URL(req.url || '/', `http://${req.headers.host || 'localhost'}`);

  if (url.pathname === '/healthz') {
    res.writeHead(200, { 'content-type': 'application/json' });
    res.end(
      JSON.stringify({
        status: 'ok',
        mode: 'simulated',
        contract_version: CONTRACT_VERSION,
        sessions_configured: Object.keys(fixtures.sessions).length,
        active_mcp_sessions: sessions.size,
      }),
    );
    return;
  }

  if (url.pathname === '/') {
    res.writeHead(200, { 'content-type': 'application/json' });
    res.end(
      JSON.stringify({
        service: 'practium-support-mcp-sim',
        mode: 'simulated',
        transport: 'streamable-http',
        endpoint: '/mcp/<session-token>',
        health: '/healthz',
        disclaimer: DISCLAIMER,
      }),
    );
    return;
  }

  if (!url.pathname.startsWith('/mcp/')) {
    res.writeHead(404, { 'content-type': 'application/json' });
    res.end(JSON.stringify({ error: 'not found' }));
    return;
  }

  if (!['POST', 'GET', 'DELETE'].includes(req.method || '')) {
    res.writeHead(405, { allow: 'POST, GET, DELETE' });
    res.end();
    return;
  }

  try {
    await handleMcp(req, res, url);
  } catch (error) {
    console.error('[mcp-sim] erro no transporte:', error);
    if (!res.headersSent) {
      jsonRpcError(res, 500, -32603, 'Erro interno do servidor MCP de simulação.');
    } else {
      res.end();
    }
  }
});

const sweeper = setInterval(() => {
  const cutoff = Date.now() - SESSION_TTL_MS;
  for (const [id, entry] of sessions.entries()) {
    if (entry.lastSeen < cutoff) {
      entry.transport.close().catch(() => {});
      sessions.delete(id);
    }
  }
}, 60_000);
sweeper.unref();

httpServer.listen(PORT, HOST, () => {
  console.log(`[mcp-sim] practium-support-mcp-sim ouvindo em http://${HOST}:${PORT}`);
  console.log(`[mcp-sim] endpoint Streamable HTTP: http://${HOST}:${PORT}/mcp/<session-token>`);
  console.log(`[mcp-sim] sessões configuradas: ${Object.keys(fixtures.sessions).length} (fixtures: ${FIXTURES_PATH})`);
});

function shutdown() {
  console.log('[mcp-sim] encerrando...');
  for (const entry of sessions.values()) entry.transport.close().catch(() => {});
  httpServer.close(() => process.exit(0));
}
process.on('SIGINT', shutdown);
process.on('SIGTERM', shutdown);

export { httpServer, fixtures };
