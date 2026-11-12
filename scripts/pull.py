#!/usr/bin/env python3
"""Traz do n8n para o repositorio o estado ATUAL dos workflows originais (anti-drift).

Le o "id" de cada JSON em assistente-suporte-tecnico/workflows/, busca esse workflow no n8n
(GET /workflows/{id}), remove campos de runtime, redige segredos e regrava o arquivo.
So le do n8n; nunca escreve nele. Depois do pull, revise com `git diff` e faca commit.

Env: N8N_URL, N8N_API_KEY
Uso: python scripts/pull.py [--check]
  --check  nao grava nada; sai com codigo 1 se algum arquivo difere do n8n (para CI/alerta)
"""
import json, os, re, sys, urllib.error, urllib.request
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
FILES = ["call-suporte.json", "hibridy-search-suport-agent.json", "assistente-suporte-tecnico.json"]
CHECK = "--check" in sys.argv

BASE = os.environ.get("N8N_URL", "").rstrip("/")
KEY = os.environ.get("N8N_API_KEY", "")
if not BASE or not KEY:
    sys.exit("Defina N8N_URL e N8N_API_KEY")

KEEP = ["id", "name", "nodes", "connections", "settings", "pinData", "tags"]
# rotulo do segredo redigido por no (mantem o texto ja usado no repositorio)
LABELS = {"Get Ocr Results": "REDACTED_MISTRAL_KEY"}
BEARER = re.compile(r"Bearer (?!REDACTED)[A-Za-z0-9._\-]{16,}")
SUSPECT = re.compile(r"sk-[A-Za-z0-9_\-]{20,}|eyJ[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{20,}")


def api(path):
    req = urllib.request.Request(f"{BASE}/api/v1{path}", headers={
        "X-N8N-API-KEY": KEY, "Accept": "application/json", "User-Agent": "n8n-pull-script/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        sys.exit(f"HTTP {e.code} em GET {path}: {e.read().decode(errors='replace')[:500]}")


def clean(wf):
    out = {k: wf[k] for k in KEEP if k in wf}
    out["tags"] = [{"name": t["name"]} for t in out.get("tags") or []]
    out["settings"] = {k: v for k, v in (out.get("settings") or {}).items()}
    for node in out["nodes"]:
        label = LABELS.get(node["name"], "REDACTED_SECRET")
        text = BEARER.sub(f"Bearer {label}", json.dumps(node))
        node.clear()
        node.update(json.loads(text))
    return out


def main():
    drift = []
    for fname in FILES:
        path = DIR / fname
        wf_id = json.loads(path.read_text())["id"]
        new = clean(api(f"/workflows/{wf_id}"))
        text = json.dumps(new, indent=2, ensure_ascii=False) + "\n"
        hit = SUSPECT.search(text)
        if hit:
            print(f"  AVISO: {fname} parece conter segredo ({hit.group()[:12]}...). Revise antes de commitar.")
        changed = not path.exists() or json.loads(path.read_text()) != new
        if changed:
            drift.append(fname)
        print(f"{'DIFERE ' if changed else 'igual  '} {fname} ({len(new['nodes'])} nos, id {wf_id})")
        if changed and not CHECK:
            path.write_text(text)
    if CHECK and drift:
        sys.exit(f"Drift em {len(drift)} arquivo(s): {', '.join(drift)}")
    if drift and not CHECK:
        print("Gravado. Revise com `git diff` e faca commit.")


if __name__ == "__main__":
    main()
