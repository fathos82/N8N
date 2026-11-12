#!/usr/bin/env python3
"""Deploy dos workflows de assistente-suporte-tecnico para COPIAS DE TESTE fixas no n8n.

Cada workflow vai para "[TEST] <nome>". Se ja existe, e atualizado (PUT) no mesmo ID;
se nao existe, e criado (POST). Nunca cria copia duplicada e nunca toca nos originais.

Env: N8N_URL (ex: https://n8n.exemplo.com), N8N_API_KEY, TEST_EMAIL_TO (destino dos e-mails do Call Suporte de teste)
Uso: python scripts/deploy.py [--dry-run]
"""
import json, os, sys, urllib.error, urllib.request, urllib.parse
from pathlib import Path


def load_env(path=Path(__file__).resolve().parent.parent / ".env"):
    """Carrega KEY=VALUE do .env da raiz. Variaveis ja definidas no ambiente tem prioridade."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.removeprefix("export ").strip()
        value = value.strip().strip('"').strip("'")
        if value and not os.environ.get(key):  # vazio no ambiente nao conta como definido
            os.environ[key] = value


load_env()

DIR = Path(__file__).resolve().parent.parent / "assistente-suporte-tecnico" / "workflows"
PREFIX = "[TEST] "
# ordem importa: dependentes primeiro, agente por ultimo
FILES = ["call-suporte.json", "hibridy-search-suport-agent.json", "assistente-suporte-tecnico.json"]
DRY = "--dry-run" in sys.argv

BASE = os.environ.get("N8N_URL", "").rstrip("/")
KEY = os.environ.get("N8N_API_KEY", "")
if not DRY and (not BASE or not KEY):
    sys.exit("Defina N8N_URL e N8N_API_KEY")
TEST_EMAIL = os.environ.get("TEST_EMAIL_TO", "")
if not DRY and not TEST_EMAIL:
    sys.exit("Defina TEST_EMAIL_TO (o Call Suporte de teste nao pode enviar para a equipe real)")


def api(method, path, body=None):
    req = urllib.request.Request(f"{BASE}/api/v1{path}", method=method,
                                 data=json.dumps(body).encode() if body is not None else None,
                                 headers={"X-N8N-API-KEY": KEY, "Content-Type": "application/json",
                                          "Accept": "application/json",
                                          "User-Agent": "n8n-deploy-script/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")[:500]
        sys.exit(f"HTTP {e.code} em {method} {path}: {detail}")


def find_by_name(name):
    cursor = None
    while True:
        q = {"limit": 100, "name": name}
        if cursor:
            q["cursor"] = cursor
        res = api("GET", "/workflows?" + urllib.parse.urlencode(q))
        hits = [w for w in res["data"] if w["name"] == name]
        if hits:
            return hits[0]["id"]
        cursor = res.get("nextCursor")
        if not cursor:
            return None


def rewrite(wf, id_map):
    out = {
        "name": PREFIX + wf["name"],
        "nodes": json.loads(json.dumps(wf["nodes"])),
        "connections": wf["connections"],
        "settings": {"executionOrder": wf.get("settings", {}).get("executionOrder", "v1")},
    }
    for n in out["nodes"]:
        p = n.get("parameters", {})
        # chamadas a sub-workflows apontam para as copias de teste
        wid = p.get("workflowId")
        if isinstance(wid, dict) and wid.get("value") in id_map:
            new = id_map[wid["value"]]
            wid["value"] = new
            wid["cachedResultUrl"] = f"/workflow/{new}"
            wid["cachedResultName"] = PREFIX + str(wid.get("cachedResultName", ""))
        # e-mail de teste nunca vai para a equipe real
        if n["type"] == "n8n-nodes-base.gmail" and "sendTo" in p:
            p["sendTo"] = TEST_EMAIL or "teste@example.invalid"
        if "REDACTED" in json.dumps(p):
            print(f"  AVISO: no '{n['name']}' tem segredo redigido; use credencial do n8n.")
    return out


def main():
    id_map = {}   # id original -> id da copia de teste
    for fname in FILES:
        wf = json.loads((DIR / fname).read_text())
        payload = rewrite(wf, id_map)
        if DRY:
            print(f"[dry-run] {payload['name']}: {len(payload['nodes'])} nos")
            id_map[wf["id"]] = "DRY"
            continue
        test_id = find_by_name(payload["name"])
        if test_id:
            api("PUT", f"/workflows/{test_id}", payload)
            print(f"atualizado {payload['name']} ({test_id})")
        else:
            test_id = api("POST", "/workflows", payload)["id"]
            print(f"criado {payload['name']} ({test_id})")
        id_map[wf["id"]] = test_id


main()
