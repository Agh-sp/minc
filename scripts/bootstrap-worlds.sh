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
  rcon 'fill -18 77 -18 18 77 18 smooth_quartz'
  rcon 'fill -16 78 -16 16 78 16 polished_deepslate'
  rcon 'fill -14 79 -14 14 79 14 smooth_quartz'
  # Cross walkways in warm oak
  rcon 'fill -2 79 -14 2 79 14 oak_planks'
  rcon 'fill -14 79 -2 14 79 2 oak_planks'
  # Stylish cyan glass railings
  rcon 'fill -15 80 -15 15 80 -15 cyan_stained_glass_pane'
  rcon 'fill -15 80 15 15 80 15 cyan_stained_glass_pane'
  rcon 'fill -15 80 -14 -15 80 14 cyan_stained_glass_pane'
  rcon 'fill 15 80 -14 15 80 14 cyan_stained_glass_pane'
  # Central fountain
  rcon 'fill -3 79 -3 3 79 3 polished_deepslate'
  rcon 'fill -2 80 -2 2 80 2 water'
  rcon 'fill -1 80 -1 1 80 1 sea_lantern'
  rcon 'fill 0 81 0 0 84 0 quartz_pillar'
  rcon 'setblock 0 85 0 sea_lantern'
  # 4 corner pillars with lanterns
  rcon 'fill -14 80 -14 -14 84 -14 quartz_pillar'
  rcon 'setblock -14 85 -14 lantern'
  rcon 'fill 14 80 -14 14 84 -14 quartz_pillar'
  rcon 'setblock 14 85 -14 lantern'
  rcon 'fill -14 80 14 -14 84 14 quartz_pillar'
  rcon 'setblock -14 85 14 lantern'
  rcon 'fill 14 80 14 14 84 14 quartz_pillar'
  rcon 'setblock 14 85 14 lantern'
  # Mini gardens in the 4 quadrants
  rcon 'fill -10 80 -10 -7 80 -7 grass_block'
  rcon 'fill -9 81 -9 -8 82 -8 oak_leaves'
  rcon 'fill 7 80 -10 10 80 -7 grass_block'
  rcon 'fill 8 81 -9 9 82 -8 oak_leaves'
  rcon 'fill -10 80 7 -7 80 10 grass_block'
  rcon 'fill -9 81 8 -8 82 9 oak_leaves'
  rcon 'fill 7 80 7 10 80 10 grass_block'
  rcon 'fill 8 81 8 9 82 9 oak_leaves'
  # 3 Mode Portals in front of spawn:
  # Center: Survival (Open, Emerald + Sea Lantern + step-on pad)
  rcon 'fill -2 80 3 -2 83 3 emerald_block'
  rcon 'fill 2 80 3 2 83 3 emerald_block'
  rcon 'fill -2 84 3 2 84 3 sea_lantern'
  rcon 'setblock 0 78 3 command_block{Command:"mv tp @p survival"}'
  rcon 'setblock 0 79 3 emerald_block'
  rcon 'setblock 0 80 3 stone_pressure_plate'
  # Left: BedWars (Locked with Iron Bars)
  rcon 'fill -9 80 3 -9 83 3 redstone_block'
  rcon 'fill -5 80 3 -5 83 3 redstone_block'
  rcon 'fill -9 84 3 -5 84 3 redstone_block'
  rcon 'fill -8 80 3 -6 83 3 iron_bars'
  # Right: Roleplay (Locked with Iron Bars)
  rcon 'fill 5 80 3 5 83 3 lapis_block'
  rcon 'fill 9 80 3 9 83 3 lapis_block'
  rcon 'fill 5 84 3 9 84 3 lapis_block'
  rcon 'fill 6 80 3 8 83 3 iron_bars'
  rcon 'setworldspawn 0 80 10'
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
