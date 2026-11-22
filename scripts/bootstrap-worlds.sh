#!/usr/bin/env bash
set -Eeuo pipefail
ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

rcon() {
  docker compose exec -T survival rcon-cli "$1"
}

printf 'منتظر آماده‌شدن Paper و RCON...\n'
ready=0
for _ in $(seq 1 90); do
  if docker compose exec -T survival rcon-cli list >/dev/null 2>&1; then
    ready=1
    break
  fi
  sleep 2
done
if ((ready == 0)); then
  printf 'RCON آماده نشد. گزارش سرور را با docker compose logs --tail=150 survival بررسی کن.\n' >&2
  exit 1
fi

rcon 'mv modify survival set gamemode survival'
rcon 'mv modify survival set difficulty normal'
printf 'دنیای Survival آماده است. بعد از ورود و /login، می‌توانید مستقیم بازی کنید.\n'
