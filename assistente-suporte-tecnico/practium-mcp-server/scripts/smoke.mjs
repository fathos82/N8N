#!/usr/bin/env node
/**
 * Smoke test contra um servidor MCP já em execução.
 *
 * Uso:
 *   MCP_BASE_URL=https://exemplo/mcp/sim-session-gamma npm run smoke
 *   MCP_BASE_URL=http://127.0.0.1:3907/mcp/sim-session-alpha npm run smoke
 *
 * O script descobre as tools, invoca as três e imprime as respostas.
 * Não grava dados, não acessa o Practium e não envia e-mail.
 */
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StreamableHTTPClientTransport } from '@modelcontextprotocol/sdk/client/streamableHttp.js';

const endpoint = process.env.MCP_BASE_URL || 'http://127.0.0.1:3907/mcp/sim-session-gamma';
const client = new Client({ name: 't007-smoke', version: '0.1.0' });
const transport = new StreamableHTTPClientTransport(new URL(endpoint));

function textOf(result) {
  return result.content?.find((item) => item.type === 'text')?.text ?? JSON.stringify(result);
}

await client.connect(transport);
console.log(`Conectado em ${endpoint.replace(/\/mcp\/.*$/, '/mcp/<token>')}`);

const tools = await client.listTools();
console.log('\nTools descobertas:');
for (const tool of tools.tools) console.log(`- ${tool.name}: ${tool.description}`);

for (const [name, args] of [
  ['get_user_context', {}],
  ['check_onboarding_dependencies', {}],
  ['get_recent_validation_errors', { window_minutes: 60 }],
]) {
  const result = await client.callTool({ name, arguments: args });
  console.log(`\n[${name}] isError=${Boolean(result.isError)}`);
  console.log(textOf(result));
}

await client.close();
