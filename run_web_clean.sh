#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

cd "$HOME/AtriaTrade"
[ -d .venv ] && source .venv/bin/activate

echo "== backup =="
ts="$(date +%Y%m%d_%H%M%S)"
cp -f src/web/app.py "src/web/app.py.bak_${ts}"

echo "== inspect current routes/helpers =="
python - <<'PY'
from src.web.app import app
for r in app.routes:
    methods = getattr(r, "methods", None)
    if methods:
        print(sorted(list(methods)), r.path)
PY

echo "== kill stale servers =="
pkill -f "uvicorn.*src.web.app" 2>/dev/null || true
pkill -f "[s]rc.web.app" 2>/dev/null || true
pkill -f "[p]ython.*src/web/app.py" 2>/dev/null || true
sleep 1

echo "== start server =="
export ATRIA_SECRET="${ATRIA_SECRET:-$(cat ~/.atria_secret 2>/dev/null || true)}"
if [ -z "${ATRIA_SECRET:-}" ]; then
  ATRIA_SECRET="$(python - <<'PY'
import secrets
print(secrets.token_hex(16))
PY
)"
  printf '%s' "$ATRIA_SECRET" > ~/.atria_secret
fi
export ATRIA_SECRET

LOG=".runlogs/atria_web_${ts}.log"
nohup python -u src/web/app.py > "$LOG" 2>&1 &
sleep 4

echo "== startup log =="
tail -n 30 "$LOG" || true

echo "== login test =="
PIN="$(grep -oP 'ADMIN_PIN\s*=\s*"\K[0-9]+' src/web/app.py | head -n1)"
cookie=".runlogs/cookie_${ts}.txt"
rm -f "$cookie"
curl -s -i -c "$cookie" -X POST "http://127.0.0.1:8080/api/auth/login" \
  -H 'Content-Type: application/json' \
  -d "{\"pin\":\"$PIN\"}" | head -n 30

echo "== action test (BUY) =="
curl -s -i -b "$cookie" -X POST "http://127.0.0.1:8080/api/action" \
  -H 'Content-Type: application/json' \
  -d '{"action":"BUY","amount":0.02}' | head -n 40

echo "== telemetry test =="
curl -s -i -b "$cookie" "http://127.0.0.1:8080/api/telemetry" | head -n 40

echo "== dashboard js endpoints =="
grep -rnoE "/api/[A-Za-z0-9_/{}?&=-]+" src/web/templates/dashboard.html src/web/static/js 2>/dev/null | sort -u || true

echo "== done =="
echo "$LOG"
