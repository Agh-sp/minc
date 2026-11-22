#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

if ! command -v docker >/dev/null 2>&1 || ! docker compose version >/dev/null 2>&1; then
  printf 'Docker Engine و Docker Compose v2 لازم است.\n' >&2
  exit 1
fi

docker compose stop survival
printf 'سرور Minecraft متوقف شد؛ دنیا و تنظیمات در پوشهٔ data باقی مانده‌اند.\n'
