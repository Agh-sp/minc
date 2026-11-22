#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

fail() {
  printf 'خطا: %s\n' "$1" >&2
  exit 1
}

if ! command -v docker >/dev/null 2>&1; then
  fail "Docker نصب نیست. Docker Engine و افزونهٔ Docker Compose v2 را روی Ubuntu نصب کن؛ راهنمای رسمی: https://docs.docker.com/engine/install/ubuntu/"
fi
if ! docker compose version >/dev/null 2>&1; then
  fail "Docker Compose v2 پیدا نشد. راهنمای رسمی: https://docs.docker.com/compose/install/linux/"
fi
if ! docker info >/dev/null 2>&1; then
  fail "به Docker دسترسی ندارم. سرویس Docker را روشن کن یا کاربرت را به گروه docker اضافه کن و دوباره وارد SSH شو."
fi

if [[ ! -f .env ]]; then
  printf '%s\n' \
    'این سرور عمومی و برای TLauncher است: ورود با نام کاربری آفلاین و رمز AuthMe انجام می‌شود.'

  read -r -p 'پورت سرور [25565]: ' mc_port
  mc_port="${mc_port:-25565}"
  [[ "$mc_port" =~ ^[0-9]+$ ]] || fail "پورت باید عدد باشد."
  ((mc_port >= 1 && mc_port <= 65535)) || fail "پورت باید بین 1 و 65535 باشد."

  printf '\nپیش از تأیید، متن توافق‌نامهٔ Minecraft را بخوان: https://aka.ms/MinecraftEULA\n'
  read -r -p 'آیا EULA را خوانده‌ای و با آن موافقی؟ برای ادامه yes بنویس: ' eula_answer
  [[ "${eula_answer,,}" == "yes" ]] || fail "بدون موافقت صریح با EULA سرور راه‌اندازی نشد."

  rcon_password="$(python3 -c 'import secrets; print(secrets.token_urlsafe(36))')"
  umask 077
  cat > .env <<EOF
EULA=TRUE
MC_PORT=$mc_port
MC_BIND=0.0.0.0
COMPOSE_PROJECT_NAME=minc-survival
RCON_PASSWORD=$rcon_password
EOF
  chmod 600 .env
  printf '\nتنظیمات خصوصی در .env ذخیره شد.\n'
else
  if ! grep -Eiq '^EULA=TRUE$' .env; then
    fail "در .env مقدار EULA=TRUE نیست. فقط اگر EULA را خوانده‌ای و قبول داری، آن را به TRUE تغییر بده."
  fi
  if ! grep -Eq '^RCON_PASSWORD=.{24,}$' .env; then
    printf 'RCON_PASSWORD=\n' >> .env
    rcon_password="$(python3 -c 'import secrets; print(secrets.token_urlsafe(36))')"
    python3 - "$rcon_password" <<'PY'
from pathlib import Path
import sys
path = Path('.env')
lines = [line for line in path.read_text(encoding='utf-8').splitlines() if not line.startswith('RCON_PASSWORD=')]
lines.append('RCON_PASSWORD=' + sys.argv[1])
path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
path.chmod(0o600)
PY
  fi
  chmod 600 .env
fi

# Run the container with the invoking Ubuntu account, not as root, so the
# persisted worlds remain manageable from the host.
if [[ "$(id -u)" == "0" ]]; then
  default_puid=1000
  default_pgid=1000
else
  default_puid="$(id -u)"
  default_pgid="$(id -g)"
fi
python3 - "$default_puid" "$default_pgid" <<'PY'
from pathlib import Path
import sys
path = Path('.env')
defaults = {'PUID': sys.argv[1], 'PGID': sys.argv[2], 'MC_BIND': '0.0.0.0', 'COMPOSE_PROJECT_NAME': 'minc-survival'}
lines = path.read_text(encoding='utf-8').splitlines()
values = {}
for line in lines:
    if '=' in line and not line.lstrip().startswith('#'):
        key, value = line.split('=', 1)
        values[key.strip()] = value.strip()
for key, value in defaults.items():
    if not values.get(key):
        if any(line.startswith(key + '=') for line in lines):
            lines = [key + '=' + value if line.startswith(key + '=') else line for line in lines]
        else:
            lines.append(key + '=' + value)
path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
path.chmod(0o600)
PY

puid="$(sed -n 's/^PUID=//p' .env | tail -n 1)"
pgid="$(sed -n 's/^PGID=//p' .env | tail -n 1)"
[[ "$puid" =~ ^[1-9][0-9]*$ ]] || fail "PUID در .env باید یک شناسهٔ کاربر عددی و غیرصفر باشد."
[[ "$pgid" =~ ^[1-9][0-9]*$ ]] || fail "PGID در .env باید یک شناسهٔ گروه عددی و غیرصفر باشد."
final_bind="$(sed -n 's/^MC_BIND=//p' .env | tail -n 1)"
python3 - "$final_bind" <<'PY' || fail "MC_BIND در .env باید یک آدرس IPv4 معتبر باشد؛ مقدار معمول 0.0.0.0 است."
import ipaddress
import sys
ipaddress.IPv4Address(sys.argv[1])
PY

if command -v ss >/dev/null 2>&1; then
  survival_cid="$(docker compose ps -q survival 2>/dev/null || true)"
  mc_running=false
  if [[ -n "$survival_cid" ]]; then
    mc_running="$(docker inspect -f '{{.State.Running}}' "$survival_cid" 2>/dev/null || true)"
  fi
  if [[ "$mc_running" != "true" ]]; then
    mc_port="$(sed -n 's/^MC_PORT=//p' .env | tail -n 1)"
    mc_port="${mc_port:-25565}"
    listeners="$(ss -H -ltn "sport = :$mc_port" 2>/dev/null || true)"
    if [[ -n "$listeners" ]]; then
      fail "پورت $mc_port از قبل در حال استفاده است. مقدار MC_PORT را در .env به یک پورت آزاد مثل 25566 تغییر بده."
    fi
  fi
fi

if [[ -r /proc/meminfo ]]; then
  available_kb="$(awk '/MemAvailable:/ {print $2; exit}' /proc/meminfo)"
  if [[ "$available_kb" =~ ^[0-9]+$ ]]; then
    available_mb=$((available_kb / 1024))
    if ((available_mb < 2300)); then
      printf 'هشدار: فقط حدود %s MiB RAM در دسترس است. سرور Minecraft تا 2 GiB می‌گیرد و بازی فعلی هم RAM مصرف می‌کند؛ ممکن است یکی از سرویس‌ها کند یا متوقف شود.\n' "$available_mb" >&2
    fi
  fi
fi

printf '\nدر حال آماده‌سازی مجوز پوشهٔ داده...\n'
mkdir -p data
if [[ "$(id -u)" == "0" ]]; then
  chown -R "$puid:$pgid" data
elif [[ "$puid" != "$(id -u)" || "$pgid" != "$(id -g)" ]]; then
  fail "مقادیر PUID/PGID باید با حساب Ubuntu اجراکنندهٔ ./start.sh برابر باشند؛ اسکریپت را بدون sudo اجرا کن یا مقدارها را در .env اصلاح کن."
fi

required_plugins=(
  AuthMe
  Multiverse-Core
  PlaceholderAPI
  DeluxeMenus
  LuckPerms
  GriefPrevention
  WorldEdit
  WorldGuard
  ProtocolLib
  ViaVersion
  ViaBackwards
  ViaRewind
)

wait_for_plugins() {
  local plugin_output missing expected
  for _ in $(seq 1 120); do
    plugin_output="$(docker compose exec -T survival rcon-cli plugins 2>/dev/null || true)"
    missing=""
    for expected in "${required_plugins[@]}"; do
      if ! grep -Fqi -- "$expected" <<< "$plugin_output"; then
        missing+="$expected "
      fi
    done
    if [[ -z "$missing" ]]; then
      return 0
    fi
    sleep 2
  done
  printf 'پلاگین‌های ضروری بالا نیامدند: %s\n' "$missing" >&2
  return 1
}

stop_on_start_failure() {
  local status=$?
  trap - ERR
  docker compose stop survival >/dev/null 2>&1 || true
  printf 'شروع امن سرور کامل نشد؛ Minecraft متوقف شد و پورت عمومی بسته ماند. جزئیات را با docker compose logs --tail=150 survival ببین.\n' >&2
  exit "$status"
}
trap stop_on_start_failure ERR

# Keep the game port private during first boot and authentication hardening.
export MC_BIND=127.0.0.1
if ! docker compose config >/dev/null; then
  docker compose stop survival >/dev/null 2>&1 || true
  fail "تنظیمات Docker Compose معتبر نیستند؛ Minecraft متوقف شد. فایل .env و docker-compose.yml را بررسی کن."
fi

printf '\nدر حال بالا آوردن لابی و دنیای Survival (فعلاً فقط روی localhost)...\n'
docker compose up -d --force-recreate survival
if ! wait_for_plugins; then
  docker compose stop survival >/dev/null 2>&1 || true
  fail "همهٔ پلاگین‌های ضروری آماده نشدند؛ سرور روی اینترنت باز نمی‌شود. گزارش را با docker compose logs --tail=150 survival بررسی کن."
fi
scripts/bootstrap-worlds.sh
scripts/harden-authme.sh
if ! wait_for_plugins; then
  docker compose stop survival >/dev/null 2>&1 || true
  fail "پلاگین‌ها پس از سخت‌سازی درست بالا نیامدند؛ سرور متوقف شد."
fi
scripts/setup-permissions.sh

printf '\nAuthMe و قفل دسترسی دنیاها تنظیم شدند. در حال بازکردن پورت بازی...\n'
unset MC_BIND
docker compose up -d --force-recreate survival
ready=0
for _ in $(seq 1 120); do
  if docker compose exec -T survival rcon-cli list >/dev/null 2>&1; then
    ready=1
    break
  fi
  sleep 2
done
if ((ready == 0)); then
  docker compose stop survival >/dev/null 2>&1 || true
  fail "سرور پس از بازکردن پورت آماده نشد؛ Minecraft متوقف شد. گزارش را با docker compose logs --tail=150 survival بررسی کن."
fi
if ! wait_for_plugins; then
  docker compose stop survival >/dev/null 2>&1 || true
  fail "یکی از پلاگین‌های ضروری پس از راه‌اندازی نهایی لود نشد؛ پورت بسته شد و سرور متوقف ماند."
fi
trap - ERR

printf '\nسرور آماده است. ابتدا /register <ramz> <ramz>، دفعات بعد /login <ramz>؛ منو: /menu.\n'
printf 'گزارش اجرا: docker compose logs -f survival\n'
printf 'توقف امن: ./stop.sh\n'
printf 'پنل خصوصی را فقط هنگام نیاز اجرا کن: ./scripts/start-panel.sh\n'
