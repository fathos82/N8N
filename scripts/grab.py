#!/usr/bin/env python3
"""grab: baixa um workflow do n8n e os sub-workflows que ele chama (executeWorkflow),
e cria uma pasta de projeto com workflows/*.json e project.json.

So le do n8n (REST). Redige segredos. Nao grava nada se a pasta ja existir.

Env: N8N_URL, N8N_API_KEY (ou .env na raiz). GRAB_OUT opcional: pasta base de saida (padrao: raiz).
Uso: python scripts/grab.py <workflow_id>
"""
import json, os, re, sys, unicodedata, urllib.error, urllib.request
from pathlib import Path


def load_env(path=Path(__file__).resolve().parent.parent / ".env"):
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.removeprefix("export ").strip()
        value = value.strip().strip('"').strip("'")
        if value and not os.environ.get(key):
            os.environ[key] = value


load_env()

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(os.environ.get("GRAB_OUT", ROOT))
PREFIX = "[TEST] "
BASE = os.environ.get("N8N_URL", "").rstrip("/")
KEY = os.environ.get("N8N_API_KEY", "")
if not BASE or not KEY:
    sys.exit("Defina N8N_URL e N8N_API_KEY (no .env ou no ambiente)")
if len(sys.argv) != 2:
    sys.exit("Uso: python scripts/grab.py <workflow_id>")

KEEP = ["id", "name", "nodes", "connections", "settings", "pinData", "tags"]
BEARER = re.compile(r"Bearer (?!REDACTED)[A-Za-z0-9._\-]{16,}")
SUSPECT = re.compile(r"sk-[A-Za-z0-9_\-]{20,}|eyJ[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{20,}")


def api(path):
    req = urllib.request.Request(f"{BASE}/api/v1{path}", headers={
        "X-N8N-API-KEY": KEY, "Accept": "application/json", "User-Agent": "n8n-grab-script/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        sys.exit(f"HTTP {e.code} em GET {path}: {e.read().decode(errors='replace')[:300]}")


def slug(name):
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def called_ids(wf):
    """IDs de sub-workflows referenciados em nos executeWorkflow (workflowId como str ou {value})."""
    found = []

    def walk(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if k == "workflowId":
                    val = v.get("value") if isinstance(v, dict) else v
                    if isinstance(val, str) and val and val not in found:
                        found.append(val)
                else:
                    walk(v)
        elif isinstance(o, list):
            for x in o:
                walk(x)

    walk(wf.get("nodes", []))
    return found


def clean(wf):
    out = {k: wf[k] for k in KEEP if k in wf}
    out["tags"] = [{"name": t["name"]} for t in out.get("tags") or []]
    for node in out["nodes"]:
        text = BEARER.sub("Bearer REDACTED_SECRET", json.dumps(node))
        node_new = json.loads(text, strict=False)
        node.clear()
        node.update(node_new)
    return out


def main():
    root_id = sys.argv[1]
    seen, order = {}, []
    queue = [root_id]
    while queue:
        wid = queue.pop(0)
        if wid in seen:
            continue
        wf = api(f"/workflows/{wid}")
        if wf["name"].startswith(PREFIX):
            sys.exit(f"O id {wid} e uma copia [TEST] ({wf['name']}). Use o original.")
        seen[wid] = wf
        order.append(wid)
        queue.extend(called_ids(wf))

    root = seen[root_id]
    folder = OUT / slug(root["name"])
    if (folder / "project.json").exists():
        sys.exit(f"A pasta {folder} ja existe. Apague-a ou use o pull para atualizar.")
    (folder / "workflows").mkdir(parents=True, exist_ok=True)

    files, subs = {}, {}
    for wid in order:
        wf = seen[wid]
        fname = f"{slug(wf['name'])}.json"
        text = json.dumps(clean(wf), indent=2, ensure_ascii=False) + "\n"
        if SUSPECT.search(text):
            print(f"  AVISO: {fname} parece conter segredo. Revise antes de commitar.")
        (folder / "workflows" / fname).write_text(text, encoding="utf-8")
        files[wid] = fname
        if wid != root_id:
            subs[wf["name"]] = f"{wid} ({wf['name']})"
        print(f"  {'principal' if wid == root_id else 'dependente'}: {wf['name']} ({len(wf['nodes'])} nos) -> workflows/{fname}")

    project = {
        "name": slug(root["name"]),
        "source_workflow": {"id": root_id, "name": root["name"], "nodes": len(root["nodes"]),
                            "active": root.get("active", False)},
        "sub_workflows": subs,
        "files": files,
        "deploy": "copias [TEST] via scripts/deploy.py",
    }
    (folder / "project.json").write_text(json.dumps(project, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Projeto criado em {folder}. Revise com git status antes de commitar.")


if __name__ == "__main__":
    main()
