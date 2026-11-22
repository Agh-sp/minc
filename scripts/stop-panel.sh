#!/usr/bin/env bash
set -Eeuo pipefail
ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

docker compose stop admin-proxy portainer
printf 'پنل مدیریت متوقف شد؛ اطلاعات ورودش در portainer-data باقی است.\n'
