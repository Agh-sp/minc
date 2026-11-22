#!/usr/bin/env python3
import hashlib
import hmac
import html
import http.cookies
import json
import os
import re
import secrets
import subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs

PANEL_USER = os.environ.get("PANEL_USER", "aziz")
PANEL_PASS = os.environ.get("PANEL_PASS", "32983298")
SECRET_KEY = os.environ.get("PANEL_SECRET", secrets.token_hex(32))
PORT = int(os.environ.get("PANEL_PORT", "8765"))
WORKDIR = Path(os.environ.get("PANEL_WORKDIR", "/workspace"))
DATA_DIR = WORKDIR / "data"


def sign_session(username: str) -> str:
    sig = hmac.new(SECRET_KEY.encode(), username.encode(), hashlib.sha256).hexdigest()
    return f"{username}:{sig}"


def verify_session(token: str) -> bool:
    if ":" not in token:
        return False
    user, sig = token.split(":", 1)
    expected = hmac.new(SECRET_KEY.encode(), user.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(sig, expected) and user == PANEL_USER


def run_cmd(args: list[str], timeout: int = 30) -> tuple[int, str]:
    try:
        res = subprocess.run(
            args,
            cwd=str(WORKDIR),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        out = (res.stdout or "") + (res.stderr or "")
        return res.returncode, out.strip()
    except Exception as exc:
        return 1, str(exc)


def rcon(command: str) -> tuple[int, str]:
    return run_cmd(["docker", "compose", "exec", "-T", "survival", "rcon-cli", command], timeout=15)


def server_status() -> str:
    code, out = run_cmd(["docker", "compose", "ps", "--status", "running", "--services"], timeout=10)
    if code == 0 and "survival" in out.splitlines():
        return "running"
    return "stopped"


def load_json_list(path: Path) -> list[dict]:
    try:
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return data
    except Exception:
        pass
    return []


def get_online_players() -> tuple[int, int, list[str]]:
    code, out = rcon("list")
    if code != 0 or not out:
        return 0, 52, []
    m = re.search(r"There are (\d+) of a max of (\d+) players online:(.*)", out)
    if not m:
        return 0, 52, []
    count = int(m.group(1))
    max_p = int(m.group(2))
    names_raw = m.group(3).strip()
    players = [n.strip() for n in names_raw.split(",") if n.strip()] if names_raw else []
    return count, max_p, players


def get_all_players(online_list: list[str]) -> list[dict]:
    online_set = {p.lower() for p in online_list}
    ops_set = {str(x.get("name", "")).lower() for x in load_json_list(DATA_DIR / "ops.json") if x.get("name")}
    banned_set = {str(x.get("name", "")).lower() for x in load_json_list(DATA_DIR / "banned-players.json") if x.get("name")}

    players_map: dict[str, str] = {}
    for entry in load_json_list(DATA_DIR / "usercache.json"):
        name = str(entry.get("name", "")).strip()
        if name:
            players_map[name.lower()] = name
    for name in online_list:
        players_map[name.lower()] = name
    for entry in load_json_list(DATA_DIR / "ops.json"):
        name = str(entry.get("name", "")).strip()
        if name:
            players_map.setdefault(name.lower(), name)
    for entry in load_json_list(DATA_DIR / "banned-players.json"):
        name = str(entry.get("name", "")).strip()
        if name:
            players_map.setdefault(name.lower(), name)

    result = []
    for key, display_name in players_map.items():
        result.append({
            "name": display_name,
            "online": key in online_set,
            "op": key in ops_set,
            "banned": key in banned_set,
        })
    result.sort(key=lambda x: (not x["online"], not x["op"], x["name"].lower()))
    return result


LOGIN_HTML = """<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>پنل مدیریت ماینکرفت</title>
<style>
  *{box-sizing:border-box;font-family:Tahoma,system-ui,sans-serif}
  body{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;background:#0f172a;color:#e2e8f0}
  .card{width:100%;max-width:360px;background:#1e293b;padding:28px;border-radius:14px;box-shadow:0 20px 40px rgba(0,0,0,.4);border:1px solid #334155}
  h1{margin:0 0 20px;font-size:20px;text-align:center;color:#38bdf8}
  label{display:block;margin-bottom:6px;font-size:13px;color:#94a3b8}
  input{width:100%;padding:10px 12px;margin-bottom:14px;border-radius:8px;border:1px solid #334155;background:#0f172a;color:#fff;font-size:14px}
  button{width:100%;padding:11px;border:0;border-radius:8px;background:#0284c7;color:#fff;font-size:15px;font-weight:bold;cursor:pointer}
  button:hover{background:#0369a1}
  .err{background:#7f1d1d;color:#fecaca;padding:8px 12px;border-radius:8px;margin-bottom:14px;font-size:13px;text-align:center}
</style>
</head>
<body>
<form class="card" method="POST" action="/login">
  <h1>پنل مدیریت سرور ماینکرفت</h1>
  {ERROR}
  <label>نام کاربری</label>
  <input name="username" required autofocus>
  <label>رمز عبور</label>
  <input name="password" type="password" required>
  <button type="submit">ورود به پنل</button>
</form>
</body>
</html>
"""

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>مدیریت سرور ماینکرفت</title>
<style>
  *{box-sizing:border-box;font-family:Tahoma,system-ui,sans-serif}
  body{margin:0;background:#0f172a;color:#e2e8f0;padding:20px}
  .wrap{max-width:1180px;margin:0 auto}
  .top{display:flex;justify-content:space-between;align-items:center;margin-bottom:18px;flex-wrap:wrap;gap:10px}
  .title{font-size:20px;font-weight:bold;color:#38bdf8}
  .badge{padding:4px 10px;border-radius:999px;font-size:12px;font-weight:bold;display:inline-block}
  .on{background:#14532d;color:#86efac}
  .off{background:#334155;color:#cbd5e1}
  .op{background:#78350f;color:#fde68a}
  .ban{background:#7f1d1d;color:#fecaca}
  .norm{background:#1e3a8a;color:#bfdbfe}
  .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:16px;margin-bottom:16px}
  .card{background:#1e293b;border:1px solid #334155;border-radius:12px;padding:18px;margin-bottom:16px}
  .card h2{margin:0 0 14px;font-size:16px;color:#f8fafc}
  .row{display:flex;gap:8px;flex-wrap:wrap;align-items:center}
  input,select{width:100%;padding:9px 11px;margin-bottom:10px;border-radius:8px;border:1px solid #334155;background:#0f172a;color:#fff;font-size:13px}
  button{padding:7px 12px;border:0;border-radius:8px;color:#fff;font-size:12px;font-weight:bold;cursor:pointer}
  .btn-green{background:#16a34a}.btn-green:hover{background:#15803d}
  .btn-red{background:#dc2626}.btn-red:hover{background:#b91c1c}
  .btn-amber{background:#d97706}.btn-amber:hover{background:#b45309}
  .btn-blue{background:#0284c7}.btn-blue:hover{background:#0369a1}
  .btn-gray{background:#475569}.btn-gray:hover{background:#334155}
  table{width:100%;border-collapse:collapse;font-size:13px}
  th,td{padding:10px 8px;border-bottom:1px solid #334155;text-align:right}
  th{color:#94a3b8;font-weight:normal}
  pre{background:#020617;border:1px solid #334155;border-radius:8px;padding:12px;overflow:auto;max-height:360px;font-family:monospace;font-size:12px;direction:ltr;text-align:left;color:#cbd5e1;white-space:pre-wrap;margin:0}
  .msg{background:#0c4a6e;color:#bae6fd;padding:10px 14px;border-radius:8px;margin-bottom:16px;font-size:13px}
</style>
<script>
function selectPlayer(name){
  document.querySelectorAll('.player-input').forEach(function(el){ el.value = name; });
}
async function refreshLogs(){
  try{
    const res = await fetch('/api/logs');
    if(res.ok){
      const txt = await res.text();
      const box = document.getElementById('logs-box');
      if(box){
        const atBottom = box.scrollHeight - box.scrollTop <= box.clientHeight + 40;
        box.textContent = txt;
        if(atBottom) box.scrollTop = box.scrollHeight;
      }
    }
  }catch(e){}
}
setInterval(refreshLogs, 5000);
</script>
</head>
<body>
<div class="wrap">
  <div class="top">
    <div class="title">پنل مدیریت سرور ماینکرفت</div>
    <div class="row">
      <span class="badge {STATUS_CLASS}">وضعیت: {STATUS_TEXT}</span>
      <span class="badge norm">آنلاین: {PLAYER_COUNT}/{MAX_PLAYERS}</span>
      <a href="/logout" style="color:#94a3b8;font-size:13px;text-decoration:none;margin-right:8px">خروج</a>
    </div>
  </div>

  {MESSAGE}

  <div class="grid">
    <div class="card" style="margin-bottom:0">
      <h2>کنترل سرور</h2>
      <div class="row" style="margin-bottom:12px">
        <form method="POST" action="/action"><input type="hidden" name="act" value="start"><button class="btn-green">روشن کردن</button></form>
        <form method="POST" action="/action"><input type="hidden" name="act" value="stop"><button class="btn-red">خاموش کردن</button></form>
        <form method="POST" action="/action"><input type="hidden" name="act" value="restart"><button class="btn-amber">ری‌استارت</button></form>
      </div>
      <form method="POST" action="/action" class="row">
        <input type="hidden" name="act" value="say">
        <input name="text" style="flex:1;margin-bottom:0" placeholder="ارسال پیام عمومی در چت سرور..." required>
        <button class="btn-blue" type="submit">ارسال</button>
      </form>
    </div>

    <div class="card" style="margin-bottom:0">
      <h2>تنظیمات دنیا (زمان، هوا، سختی)</h2>
      <div class="row" style="margin-bottom:8px">
        <form method="POST" action="/action"><input type="hidden" name="act" value="cmd"><input type="hidden" name="command" value="time set day"><button class="btn-amber">روز</button></form>
        <form method="POST" action="/action"><input type="hidden" name="act" value="cmd"><input type="hidden" name="command" value="time set night"><button class="btn-gray">شب</button></form>
        <form method="POST" action="/action"><input type="hidden" name="act" value="cmd"><input type="hidden" name="command" value="weather clear"><button class="btn-blue">آفتابی</button></form>
        <form method="POST" action="/action"><input type="hidden" name="act" value="cmd"><input type="hidden" name="command" value="weather rain"><button class="btn-gray">بارانی</button></form>
      </div>
      <form method="POST" action="/action" class="row">
        <input type="hidden" name="act" value="difficulty">
        <select name="diff" style="flex:1;margin-bottom:0">
          <option value="peaceful">Peaceful (صلح‌آمیز)</option>
          <option value="easy">Easy (آسان)</option>
          <option value="normal" selected>Normal (معمولی)</option>
          <option value="hard">Hard (سخت)</option>
        </select>
        <button class="btn-blue" type="submit">تغییر سختی</button>
      </form>
    </div>

    <div class="card" style="margin-bottom:0">
      <h2>دادن آیتم و گیم‌مود</h2>
      <form method="POST" action="/action" style="margin-bottom:10px">
        <input type="hidden" name="act" value="give">
        <input class="player-input" name="player" placeholder="نام بازیکن" required>
        <div class="row">
          <input name="item" style="flex:2;margin-bottom:0" placeholder="آیتم (diamond)" required>
          <input name="amount" type="number" value="64" min="1" max="6400" style="flex:1;margin-bottom:0" required>
          <button class="btn-green" type="submit">ارسال</button>
        </div>
      </form>
      <form method="POST" action="/action" class="row">
        <input type="hidden" name="act" value="gamemode">
        <input class="player-input" name="player" style="flex:1;margin-bottom:0" placeholder="نام بازیکن" required>
        <select name="mode" style="flex:1;margin-bottom:0">
          <option value="survival">Survival</option>
          <option value="creative">Creative</option>
          <option value="adventure">Adventure</option>
          <option value="spectator">Spectator</option>
        </select>
        <button class="btn-blue" type="submit">تغییر</button>
      </form>
    </div>
  </div>

  <div class="card">
    <h2>تمام بازیکنان (آنلاین، آفلاین، مدیران و بن‌شده‌ها)</h2>
    <div style="overflow-x:auto">
      <table>
        <thead>
          <tr>
            <th>نام بازیکن</th>
            <th>وضعیت اتصال</th>
            <th>نقش</th>
            <th>وضعیت بن</th>
            <th>عملیات سریع</th>
          </tr>
        </thead>
        <tbody>
          {PLAYERS_ROWS}
        </tbody>
      </table>
    </div>
  </div>

  <div class="card">
    <div class="top" style="margin-bottom:10px">
      <h2 style="margin:0">ترمینال و لاگ زنده (چت‌ها و رویدادهای سرور)</h2>
      <button type="button" class="btn-blue" onclick="refreshLogs()">به‌روزرسانی</button>
    </div>
    <pre id="logs-box">{LOGS}</pre>
    <form method="POST" action="/action" class="row" style="margin-top:12px">
      <input type="hidden" name="act" value="cmd">
      <input name="command" style="flex:1;margin-bottom:0;direction:ltr" placeholder="دستور کنسول: say Salam! | op user | deop user | tp user1 user2" required>
      <button class="btn-blue" type="submit">اجرای دستور</button>
    </form>
  </div>
</div>
</body>
</html>
"""


class PanelHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def is_auth(self) -> bool:
        cookie_header = self.headers.get("Cookie", "")
        c = http.cookies.SimpleCookie()
        c.load(cookie_header)
        morsel = c.get("minc_session")
        return bool(morsel and verify_session(morsel.value))

    def send_html(self, body: str, status: int = 200, headers: dict | None = None):
        data = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        if headers:
            for k, v in headers.items():
                self.send_header(k, v)
        self.end_headers()
        self.wfile.write(data)

    def redirect(self, location: str, headers: dict | None = None):
        self.send_response(303)
        self.send_header("Location", location)
        if headers:
            for k, v in headers.items():
                self.send_header(k, v)
        self.end_headers()

    def build_players_rows(self, players: list[dict]) -> str:
        if not players:
            return '<tr><td colspan="5" style="color:#94a3b8;text-align:center">هنوز هیچ بازیکنی وارد سرور نشده است.</td></tr>'
        rows = []
        for p in players:
            name_esc = html.escape(p["name"])
            conn_badge = '<span class="badge on">آنلاین</span>' if p["online"] else '<span class="badge off">آفلاین</span>'
            role_badge = '<span class="badge op">مدیر (OP)</span>' if p["op"] else '<span class="badge norm">کاربر عادی</span>'
            ban_badge = '<span class="badge ban">بن شده</span>' if p["banned"] else '<span class="badge off">آزاد</span>'
            op_btn = (
                f'<form method="POST" action="/action" style="display:inline"><input type="hidden" name="player" value="{name_esc}"><button class="btn-gray" name="act" value="deop">برداشتن OP</button></form>'
                if p["op"]
                else f'<form method="POST" action="/action" style="display:inline"><input type="hidden" name="player" value="{name_esc}"><button class="btn-blue" name="act" value="op">OP</button></form>'
            )
            ban_btn = (
                f'<form method="POST" action="/action" style="display:inline"><input type="hidden" name="player" value="{name_esc}"><button class="btn-green" name="act" value="pardon">Unban</button></form>'
                if p["banned"]
                else f'<form method="POST" action="/action" style="display:inline"><input type="hidden" name="player" value="{name_esc}"><button class="btn-red" name="act" value="ban">Ban</button></form>'
            )
            kick_btn = (
                f'<form method="POST" action="/action" style="display:inline"><input type="hidden" name="player" value="{name_esc}"><button class="btn-amber" name="act" value="kick">Kick</button></form>'
                if p["online"]
                else ""
            )
            sel_btn = f'<button type="button" class="btn-gray" onclick="selectPlayer(\'{name_esc}\')">انتخاب</button>'
            sponsor_btn = f'<form method="POST" action="/action" style="display:inline"><input type="hidden" name="player" value="{name_esc}"><button class="btn-amber" name="act" value="sponsor">کیت اسپانسر</button></form>'
            rows.append(
                f"<tr><td><strong>{name_esc}</strong></td><td>{conn_badge}</td><td>{role_badge}</td><td>{ban_badge}</td>"
                f'<td><div class="row">{sel_btn}{op_btn}{sponsor_btn}{kick_btn}{ban_btn}</div></td></tr>'
            )
        return "\n".join(rows)

    def render_dashboard(self, msg: str = "") -> str:
        st = server_status()
        status_class = "on" if st == "running" else "off"
        status_text = "روشن" if st == "running" else "خاموش"
        count, max_p, online_list = get_online_players() if st == "running" else (0, 52, [])
        all_players = get_all_players(online_list)
        players_rows = self.build_players_rows(all_players)
        _, logs = run_cmd(["docker", "compose", "logs", "--tail=120", "--no-color", "survival"], timeout=10)
        msg_html = f'<div class="msg">{html.escape(msg)}</div>' if msg else ""
        return (
            DASHBOARD_HTML.replace("{STATUS_CLASS}", status_class)
            .replace("{STATUS_TEXT}", status_text)
            .replace("{PLAYER_COUNT}", str(count))
            .replace("{MAX_PLAYERS}", str(max_p))
            .replace("{PLAYERS_ROWS}", players_rows)
            .replace("{MESSAGE}", msg_html)
            .replace("{LOGS}", html.escape(logs or "لاگی موجود نیست."))
        )

    def do_GET(self):
        if self.path == "/logout":
            self.redirect("/", {"Set-Cookie": "minc_session=; Path=/; Max-Age=0"})
            return
        if not self.is_auth():
            if self.path == "/api/logs":
                self.send_response(401)
                self.end_headers()
                return
            self.send_html(LOGIN_HTML.replace("{ERROR}", ""))
            return
        if self.path == "/api/logs":
            _, logs = run_cmd(["docker", "compose", "logs", "--tail=120", "--no-color", "survival"], timeout=10)
            data = (logs or "لاگی موجود نیست.").encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        self.send_html(self.render_dashboard())

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8", errors="replace")
        form = {k: v[0] for k, v in parse_qs(raw).items()}

        if self.path == "/login":
            user = form.get("username", "").strip()
            pw = form.get("password", "")
            if user == PANEL_USER and pw == PANEL_PASS:
                token = sign_session(user)
                self.redirect("/", {"Set-Cookie": f"minc_session={token}; Path=/; HttpOnly"})
            else:
                err = '<div class="err">نام کاربری یا رمز عبور اشتباه است.</div>'
                self.send_html(LOGIN_HTML.replace("{ERROR}", err), status=401)
            return

        if not self.is_auth():
            self.redirect("/")
            return

        act = form.get("act", "")
        msg = ""
        if act == "start":
            _, out = run_cmd(["docker", "compose", "start", "survival"], timeout=30)
            msg = f"سرور روشن شد. {out}"
        elif act == "stop":
            _, out = run_cmd(["docker", "compose", "stop", "survival"], timeout=60)
            msg = f"سرور خاموش شد. {out}"
        elif act == "restart":
            _, out = run_cmd(["docker", "compose", "restart", "survival"], timeout=60)
            msg = f"سرور ری‌استارت شد. {out}"
        elif act in ("op", "deop", "kick", "ban", "pardon", "kill"):
            p = form.get("player", "").strip()
            _, out = rcon(f"{act} {p}")
            msg = out or f"دستور {act} {p} اجرا شد."
        elif act == "sponsor":
            p = form.get("player", "").strip()
            _, out = rcon(f"lp user {p} permission set essentials.kits.sponsor true")
            msg = out or f"دسترسی کیت اسپانسر به {p} داده شد."
        elif act == "give":
            p = form.get("player", "").strip()
            item = form.get("item", "").strip()
            amt = form.get("amount", "1").strip()
            _, out = rcon(f"give {p} {item} {amt}")
            msg = out or f"آیتم {item} به تعداد {amt} برای {p} ارسال شد."
        elif act == "gamemode":
            p = form.get("player", "").strip()
            m = form.get("mode", "survival").strip()
            _, out = rcon(f"gamemode {m} {p}")
            msg = out or f"گیم‌مود {p} به {m} تغییر کرد."
        elif act == "difficulty":
            d = form.get("diff", "normal").strip()
            _, out = rcon(f"difficulty {d}")
            msg = out or f"سختی بازی به {d} تغییر کرد."
        elif act == "say":
            t = form.get("text", "").strip()
            _, out = rcon(f"say {t}")
            msg = out or "پیام ارسال شد."
        elif act == "cmd":
            cmd = form.get("command", "").strip()
            _, out = rcon(cmd)
            msg = out or f"دستور '{cmd}' اجرا شد."

        self.send_html(self.render_dashboard(msg))


if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", PORT), PanelHandler)
    print(f"Minecraft Admin Panel listening on 0.0.0.0:{PORT}")
    server.serve_forever()
