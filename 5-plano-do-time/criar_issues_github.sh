#!/usr/bin/env bash
# Cria labels, marcos (milestones) e as 25 issues do plano no repositório indicado.
# Uso: ./criar_issues_github.sh dono/repositorio
# Requer: GitHub CLI (gh) autenticado e python3.
set -euo pipefail
REPO="${1:?Informe o repositório, ex.: minha-org/astrohealth}"
CSV="$(dirname "$0")/issues-astrohealth.csv"

for l in dados-e-ia telas back-end entrega astrohealth; do
  gh label create "$l" --repo "$REPO" --force >/dev/null
done

python3 - "$REPO" "$CSV" <<'PY'
import csv, subprocess, sys, json
repo, path = sys.argv[1], sys.argv[2]
rows = list(csv.DictReader(open(path, encoding="utf-8")))
existentes = {m["title"] for m in json.loads(subprocess.check_output(
    ["gh", "api", f"repos/{repo}/milestones?state=all&per_page=100"]))}
for marco, prazo in sorted({(r["Marco"], r["Prazo"]) for r in rows}, key=lambda x: x[1]):
    if marco not in existentes:
        subprocess.check_call(["gh", "api", f"repos/{repo}/milestones", "-f", f"title={marco}",
                               "-f", f"due_on={prazo}T23:59:00Z"], stdout=subprocess.DEVNULL)
for r in rows:
    subprocess.check_call(["gh", "issue", "create", "--repo", repo, "--title", r["Titulo"],
                           "--body", r["Descricao"], "--label", r["Labels"].replace(";", ","),
                           "--milestone", r["Marco"]])
print(f"{len(rows)} issues criadas em {repo}")
PY
