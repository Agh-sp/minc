#!/usr/bin/env bash
set -Eeuo pipefail
ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if ! command -v docker >/dev/null 2>&1 || ! docker compose version >/dev/null 2>&1; then
  printf 'Docker Engine و Docker Compose v2 لازم است.\n' >&2
  exit 1
fi

docker compose --profile admin up -d admin-panel
printf '\nپنل مدیریت اختصاصی ماینکرفت روشن شد.\n'
printf 'آدرس ورود: http://SERVER_IP:8765\n'
printf 'نام کاربری: aziz\n'
printf 'رمز عبور: 32983298\n'
