#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

ready=0
for _ in $(seq 1 90); do
  if docker compose exec -T survival rcon-cli list >/dev/null 2>&1; then
    ready=1
    break
  fi
  sleep 2
done
if ((ready == 0)); then
  printf 'RCON آماده نیست؛ تنظیم LuckPerms انجام نشد.\n' >&2
  exit 1
fi

run() {
  local command="$1"
  docker compose exec -T survival rcon-cli "$command"
}

# Only Survival and the lobby are accessible to the default (non-OP) group.
# Multiverse has enforce-access and teleport-intercept enabled before the public port opens.
run 'lp group default permission set multiverse.access.lobby true'
run 'lp group default permission set multiverse.access.survival true'
run 'lp group default permission set multiverse.access.bedwars false'
run 'lp group default permission set multiverse.access.roleplay false'
# Multiverse 5.8 requires both the destination-type node and the world-specific node.
run 'lp group default permission set multiverse.teleport.self.w true'
run 'lp group default permission set multiverse.teleport.self.w.lobby true'
run 'lp group default permission set multiverse.teleport.self.w.survival true'
run 'lp group default permission set multiverse.teleport.self.w.bedwars false'
run 'lp group default permission set multiverse.teleport.self.w.roleplay false'

# Public menu access; do not grant /dm open or other DeluxeMenus admin commands.
run 'lp group default permission set deluxemenus.guimenucommand true'
run 'lp group default permission set deluxemenus.guimenu.modes true'

# Basic Survival claims and player-quality-of-life commands only.
run 'lp group default permission set griefprevention.claims true'
run 'lp group default permission set griefprevention.createclaims true'
run 'lp group default permission set huskhomes.command.home true'
run 'lp group default permission set huskhomes.command.sethome true'
run 'lp group default permission set huskhomes.command.delhome true'
run 'lp group default permission set huskhomes.command.homelist true'
run 'lp group default permission set huskhomes.command.tpa true'
run 'lp group default permission set huskhomes.command.tpahere true'
run 'lp group default permission set huskhomes.command.tpaccept true'
run 'lp group default permission set huskhomes.command.tpdecline true'
run 'lp group default permission set huskhomes.command.tpignore true'
run 'lp group default permission set huskhomes.command.back true'
run 'lp group default permission set huskhomes.command.rtp true'
run 'lp group default permission set huskhomes.max_homes.3 true'

printf 'LuckPerms default group configured: lobby/Survival open; BedWars/Roleplay denied.\n'
