import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { once } from 'node:events';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StreamableHTTPClientTransport } from '@modelcontextprotocol/sdk/client/streamableHttp.js';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const SERVER = path.join(HERE, '..', 'src', 'server.js');
const PORT = 39000 + Math.floor(Math.random() * 500);
const BASE = `http://127.0.0.1:${PORT}`;

let child;

async function waitForHealth() {
  for (let i = 0; i < 50; i += 1) {
    try {
      const response = await fetch(`${BASE}/healthz`);
      if (response.ok) return;
    } catch {
      // servidor ainda subindo
    }
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
  throw new Error('Servidor MCP não respondeu em /healthz.');
}

async function connect(token) {
  const client = new Client({ name: 't007-test-client', version: '0.1.0' });
  const transport = new StreamableHTTPClientTransport(new URL(`${BASE}/mcp/${token}`));
  await client.connect(transport);
  return client;
}

function parseToolResult(result) {
  const text = result.content?.find((item) => item.type === 'text')?.text;
  assert.ok(text, 'tool deve retornar conteúdo textual');
  return JSON.parse(text);
}

before(async () => {
  child = spawn(process.execPath, [SERVER], {
    env: { ...process.env, PORT: String(PORT), HOST: '127.0.0.1' },
    stdio: ['ignore', 'pipe', 'pipe'],
  });
  child.stdout.setEncoding('utf8');
  child.stderr.setEncoding('utf8');
  await waitForHealth();
});

after(async () => {
  if (child && !child.killed) {
    child.kill('SIGTERM');
    await Promise.race([once(child, 'exit'), new Promise((r) => setTimeout(r, 2000))]);
  }
});

test('Caso 1: sessão fictícia com análise de solo ausente', async () => {
  const client = await connect('sim-session-alpha');
  try {
    const tools = await client.listTools();
    assert.deepEqual(
      tools.tools.map((tool) => tool.name).sort(),
      ['check_onboarding_dependencies', 'get_recent_validation_errors', 'get_user_context'],
    );

    const context = parseToolResult(await client.callTool({ name: 'get_user_context', arguments: {} }));
    assert.equal(context.simulated, true);
    assert.equal(context.user.role, 'gestor_business');
    assert.equal(context.user.plan, 'business');

    const onboarding = parseToolResult(
      await client.callTool({ name: 'check_onboarding_dependencies', arguments: {} }),
    );
    assert.equal(onboarding.simulated, true);
    assert.equal(onboarding.all_satisfied, false);
    assert.deepEqual(onboarding.missing_steps, ['soil_analysis']);
    assert.equal(onboarding.next_recommended_step.target_step, 'soil_analysis');
    assert.match(onboarding.next_recommended_step.message, /análise de solo/i);

    const errors = parseToolResult(
      await client.callTool({ name: 'get_recent_validation_errors', arguments: { window_minutes: 60 } }),
    );
    assert.equal(errors.count, 0);
    assert.deepEqual(errors.errors, []);
  } finally {
    await client.close();
  }
});

test('Caso 2: erro de validação retornado e falha simulada não inventa diagnóstico', async () => {
  const beta = await connect('sim-session-beta');
  try {
    const errors = parseToolResult(
      await beta.callTool({ name: 'get_recent_validation_errors', arguments: { window_minutes: 60 } }),
    );
    assert.equal(errors.count, 1);
    assert.equal(errors.errors[0].field, 'Fósforo (P)');
    assert.match(errors.errors[0].message, /numérico positivo/);
    assert.match(errors.errors[0].screen, /analise-solo/);
  } finally {
    await beta.close();
  }

  const degraded = await connect('sim-session-degraded');
  try {
    const failed = await degraded.callTool({
      name: 'get_recent_validation_errors',
      arguments: { window_minutes: 60 },
    });
    assert.equal(failed.isError, true);
    const payload = parseToolResult(failed);
    assert.equal(payload.error.code, 'SIMULATED_BACKEND_UNAVAILABLE');
    assert.equal(payload.errors, undefined);
    assert.match(payload.error.message, /Não há diagnóstico disponível/i);
  } finally {
    await degraded.close();
  }
});

test('Caso 3: sessão desconhecida e identidade divergente são rejeitadas sem dados', async () => {
  await assert.rejects(
    () => connect('sim-session-desconhecida'),
    (error) => /401|Unauthorized|Sessão desconhecida/i.test(String(error?.message || error)),
  );

  const alpha = await connect('sim-session-alpha');
  try {
    const mismatch = await alpha.callTool({
      name: 'get_user_context',
      arguments: { user_id: 'user_bruno_ficticio' },
    });
    assert.equal(mismatch.isError, true);
    const payload = parseToolResult(mismatch);
    assert.equal(payload.error.code, 'IDENTITY_MISMATCH');
    assert.equal(payload.user, undefined);
    assert.equal(payload.requested_user_id, undefined);
  } finally {
    await alpha.close();
  }

  // Sessão de transporte criada para alpha não pode ser reutilizada contra o token de beta.
  const initializeResponse = await fetch(`${BASE}/mcp/sim-session-alpha`, {
    method: 'POST',
    headers: {
      'content-type': 'application/json',
      accept: 'application/json, text/event-stream',
    },
    body: JSON.stringify({
      jsonrpc: '2.0',
      id: 1,
      method: 'initialize',
      params: {
        protocolVersion: '2025-06-18',
        capabilities: {},
        clientInfo: { name: 'raw-test', version: '0.1.0' },
      },
    }),
  });
  assert.equal(initializeResponse.status, 200);
  const sessionId = initializeResponse.headers.get('mcp-session-id');
  assert.ok(sessionId, 'initialize deve devolver mcp-session-id');

  const crossToken = await fetch(`${BASE}/mcp/sim-session-beta`, {
    method: 'POST',
    headers: {
      'content-type': 'application/json',
      accept: 'application/json, text/event-stream',
      'mcp-session-id': sessionId,
    },
    body: JSON.stringify({ jsonrpc: '2.0', id: 2, method: 'tools/list', params: {} }),
  });
  assert.equal(crossToken.status, 403);
  const crossPayload = await crossToken.json();
  assert.match(crossPayload.error.message, /Identidade divergente/i);
});
