#!/usr/bin/env python3
"""Traz do n8n para o repositorio o estado atual dos workflows (anti-drift).

Modo padrao: le os ORIGINAIS (ids em assistente-suporte-tecnico/workflows/*.json).
Modo --from-test: le as COPIAS [TEST] e desfaz as trocas do deploy (nome, IDs de
sub-workflow e e-mail de teste), usando os IDs originais de project.json e o e-mail
real do call-suporte.json local.

So le do n8n; nunca escreve nele. Depois do pull, revise com `git diff` e faca commit.

Env: N8N_URL, N8N_API_KEY, TEST_EMAIL_TO (obrigatorio com --from-test); ou um .env na raiz.
Uso: python scripts/pull.py [--check] [--from-test]
  --check  nao grava nada; sai com codigo 1 se algum arquivo difere do n8n
"""
import json, os, re, sys, urllib.error, urllib.parse, urllib.request
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
FILES = ["call-suporte.json", "hibridy-search-suport-agent.json", "assistente-suporte-tecnico.json"]
CHECK = "--check" in sys.argv
FROM_TEST = "--from-test" in sys.argv

BASE = os.environ.get("N8N_URL", "").rstrip("/")
KEY = os.environ.get("N8N_API_KEY", "")
TEST_EMAIL = os.environ.get("TEST_EMAIL_TO", "")
if not BASE or not KEY:
    sys.exit("Defina N8N_URL e N8N_API_KEY")
if FROM_TEST and not TEST_EMAIL:
    sys.exit("--from-test precisa de TEST_EMAIL_TO (para reconhecer e desfazer o e-mail de teste)")

KEEP = ["id", "name", "nodes", "connections", "settings", "pinData", "tags"]
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


def find_by_name(name):
    cursor = None
    while True:
        q = {"limit": 100, "name": name}
        if cursor:
            q["cursor"] = cursor
        res = api("/workflows?" + urllib.parse.urlencode(q))
        hits = [w for w in res["data"] if w["name"] == name]
        if hits:
            return hits[0]["id"]
        cursor = res.get("nextCursor")
        if not cursor:
            return None


def original_ids():
    """IDs originais, vindos do project.json (fonte de verdade dos ids)."""
    p = json.loads((DIR.parent / "project.json").read_text(encoding="utf-8"))
    sub = p["sub_workflows"]
    return {
        "assistente-suporte-tecnico.json": p["source_workflow"]["id"],
        "hibridy-search-suport-agent.json": sub["knowledgeBase"].split()[0],
        "call-suporte.json": sub["Call Suporte"].split()[0],
    }


def make_fix(id_map, real_email):
    """Desfaz no texto dos nos as trocas do deploy: IDs de copia, prefixo e e-mail de teste."""
    def fix(text):
        for test_id, orig_id in id_map.items():
            text = text.replace(test_id, orig_id)
        text = text.replace(PREFIX, "")
        return text.replace(TEST_EMAIL, real_email)
    return fix


def clean(wf, fix):
    out = {k: wf[k] for k in KEEP if k in wf}
    out["tags"] = [{"name": t["name"]} for t in out.get("tags") or []]
    out["settings"] = {k: v for k, v in (out.get("settings") or {}).items()}
    for node in out["nodes"]:
        label = LABELS.get(node["name"], "REDACTED_SECRET")
        text = fix(BEARER.sub(f"Bearer {label}", json.dumps(node)))
        node.clear()
        node.update(json.loads(text, strict=False))
    return out


def main():
    origs = original_ids()
    cs = json.loads((DIR / "call-suporte.json").read_text(encoding="utf-8"), strict=False)
    real_email = next((n["parameters"].get("sendTo") for n in cs["nodes"]
                       if n.get("type") == "n8n-nodes-base.gmail"), None)
    if FROM_TEST and (not real_email or real_email == TEST_EMAIL):
        sys.exit("E-mail real nao encontrado em call-suporte.json (ou e o de teste). Corrija antes.")

    # resolve de onde ler cada arquivo
    source = {}
    for fname in FILES:
        local = json.loads((DIR / fname).read_text(encoding="utf-8"), strict=False)
        if FROM_TEST:
            copy_id = find_by_name(PREFIX + local["name"])
            if not copy_id:
                sys.exit(f"Copia {PREFIX}{local['name']} nao encontrada no n8n")
            source[fname] = copy_id
        else:
            source[fname] = local["id"]

    id_map = {source[f]: origs[f] for f in FILES} if FROM_TEST else {}
    fix = make_fix(id_map, real_email) if FROM_TEST else (lambda t: t)

    drift = []
    for fname in FILES:
        path = DIR / fname
        new = clean(api(f"/workflows/{source[fname]}"), fix)
        if FROM_TEST:
            new["id"] = origs[fname]
            new["name"] = new["name"].removeprefix(PREFIX)
        elif new["name"].startswith(PREFIX):
            sys.exit(f"{fname}: o id {source[fname]} aponta para uma copia [TEST]. Corrija o campo id.")
        text = json.dumps(new, indent=2, ensure_ascii=False) + "\n"
        if SUSPECT.search(text):
            print(f"  AVISO: {fname} parece conter segredo. Revise antes de commitar.")
        changed = not path.exists() or json.loads(path.read_text(encoding="utf-8"), strict=False) != new
        if changed:
            drift.append(fname)
        print(f"{'DIFERE ' if changed else 'igual  '} {fname} ({len(new['nodes'])} nos, id {new['id']})")
        if changed and not CHECK:
            path.write_text(text, encoding="utf-8")
    if CHECK and drift:
        sys.exit(f"Drift em {len(drift)} arquivo(s): {', '.join(drift)}")
    if drift and not CHECK:
        print("Gravado. Revise com `git diff` e faca commit.")


if __name__ == "__main__":
    main()
