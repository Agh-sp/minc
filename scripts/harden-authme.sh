#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

# Keep any direct invocation private too; start.sh exposes the port only after checks.
export MC_BIND=127.0.0.1

configs=(
  data/plugins/AuthMe/config.yml
  data/plugins/Multiverse-Core/config.yml
  data/plugins/HuskHomes/config.yml
  data/plugins/GriefPrevention/config.yml
)

ready=0
for _ in $(seq 1 120); do
  ready=1
  for config in "${configs[@]}"; do
    if [[ ! -f "$config" ]]; then
      ready=0
      break
    fi
  done
  ((ready == 1)) && break
  sleep 2
done

if ((ready == 0)); then
  docker compose stop survival >/dev/null 2>&1 || true
  printf 'A required plugin config was not generated; the offline-mode server has been stopped for safety. Check the plugin downloads and logs.\n' >&2
  exit 1
fi

docker compose stop survival
if ! python3 scripts/harden-authme.py data/plugins; then
  docker compose stop survival >/dev/null 2>&1 || true
  printf 'Security and world-access settings could not be confirmed; the offline-mode server remains stopped.\n' >&2
  exit 1
fi
docker compose up -d survival
printf 'AuthMe and Survival world-protection settings applied; server restarted privately.\n'
