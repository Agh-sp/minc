#!/usr/bin/env bash
set -Eeuo pipefail
ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if ! command -v docker >/dev/null 2>&1 || ! docker compose version >/dev/null 2>&1; then
  printf 'Docker Engine و Docker Compose v2 لازم است.\n' >&2
  exit 1
fi

docker compose --profile admin up -d portainer admin-proxy
printf '\nپنل فقط روی خود سرور باز است. از رایانهٔ خودت تونل SSH بساز:\n'
printf '  ssh -N -L 8765:127.0.0.1:8765 SSH_USER@SERVER_IP\n'
printf 'بعد در مرورگر باز کن: http://localhost:8765/panl/\n'
printf 'در اولین ورود، حساب مدیر را خودت بساز. پنل به Docker دسترسی مدیریتی کامل دارد.\n'
