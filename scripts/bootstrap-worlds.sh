#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

rcon() {
  docker compose exec -T survival rcon-cli "$1"
}

printf 'منتظر آماده‌شدن Paper و RCON...\n'
ready=0
for _ in $(seq 1 120); do
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

if [[ ! -f data/survival/level.dat ]]; then
  printf 'در حال ساخت دنیای Survival...\n'
  rcon 'mv create survival normal' || true
  created=0
  for _ in $(seq 1 90); do
    if [[ -f data/survival/level.dat || -d data/survival ]]; then
      created=1
      break
    fi
    sleep 2
  done
  if ((created == 0)); then
    printf 'Multiverse نتوانست دنیای survival را بسازد. بررسی کن پلاگین Multiverse-Core بدون خطا بارگذاری شده باشد.\n' >&2
    exit 1
  fi
fi

# The lobby is built once in the flat lobby world. Remove data/.lobby-built to rebuild it.
if [[ ! -f data/.lobby-built ]]; then
  printf 'در حال ساخت لابی شروع...\n'
  rcon 'fill -20 76 -20 20 76 20 polished_deepslate'
  rcon 'fill -19 77 -19 19 77 19 smooth_quartz'
  rcon 'fill -17 78 -17 17 78 17 quartz_block'
  rcon 'fill -15 79 -15 15 79 15 white_concrete'
  rcon 'fill -15 80 -15 15 81 -15 glass'
  rcon 'fill -15 80 15 15 81 15 glass'
  rcon 'fill -15 80 -14 -15 81 14 glass'
  rcon 'fill 15 80 -14 15 81 14 glass'
  rcon 'fill -1 80 -1 1 80 1 sea_lantern'
  rcon 'fill 0 81 0 0 84 0 quartz_pillar'
  rcon 'setblock 0 85 0 sea_lantern'
  rcon 'fill -11 80 4 -7 80 8 emerald_block'
  rcon 'fill -2 80 4 2 80 8 redstone_block'
  rcon 'fill 7 80 4 11 80 8 lapis_block'
  rcon 'setblock -14 80 -14 sea_lantern'
  rcon 'setblock 14 80 -14 sea_lantern'
  rcon 'setblock -14 80 14 sea_lantern'
  rcon 'setblock 14 80 14 sea_lantern'
  rcon 'setworldspawn 0 80 12'
  rcon 'gamerule doMobSpawning false'
  rcon 'gamerule doDaylightCycle false'
  rcon 'gamerule mobGriefing false'
  rcon 'time set day'
  rcon 'weather clear'
  touch data/.lobby-built
fi

# Keep the hub safe and put normal survival rules in the Survival world.
rcon 'mv modify lobby set gamemode adventure'
rcon 'mv modify survival set gamemode survival'
rcon 'mv modify lobby set difficulty peaceful'
rcon 'mv modify survival set difficulty normal'

# WorldGuard's global region is per-world. Keep the entire flat lobby protected,
# while allowing normal Survival building and PvP rules.
rcon 'rg flag __global__ passthrough -w lobby deny'
rcon 'rg flag __global__ pvp -w lobby deny'
rcon 'rg flag __global__ mob-spawning -w lobby deny'
rcon 'rg flag __global__ use -w lobby allow'
rcon 'rg flag __global__ item-drop -w lobby deny'
rcon 'rg flag __global__ item-pickup -w lobby deny'
printf 'لابی و دنیای Survival آماده‌اند. بعد از ورود و /login، دستور /menu را بزن.\n'
