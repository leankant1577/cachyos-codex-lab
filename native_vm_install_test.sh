#!/usr/bin/bash
# Only in the isolated VM launched with the CODEX-SMOKE-ONLY virtual disk.
set -euo pipefail
trap 'printf "%s\n" "$?" >/tmp/native-install-test.exit' EXIT
until systemctl is-active --quiet multi-user.target; do sleep 2; done
bash /tmp/guest-smoke-checks.sh >/tmp/native-smoke-test.log 2>&1
if [[ ! -f /run/codex-cachyos/credentials.json ]]; then
    /usr/local/bin/codex-cachyos credenciais /tmp/codex-smoke-plan.json >/tmp/native-credential-test.log 2>&1
fi
digest=$(python - <<'PY'
import hashlib, json
from pathlib import Path
plan=json.loads(Path('/tmp/codex-smoke-plan.json').read_text())
assert plan['target']['serial']=='CODEX-SMOKE-ONLY'
assert plan['target']['size_bytes']==34359738368
print(hashlib.sha256(json.dumps(plan,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()).hexdigest())
PY
)
/usr/local/bin/codex-cachyos instalar /tmp/codex-smoke-plan.json --aprovado-sha256 "$digest" >/tmp/native-controller-test.log 2>&1
printf 'NATIVE_INSTALL_AND_PERSISTENCE_PASSED\n'
