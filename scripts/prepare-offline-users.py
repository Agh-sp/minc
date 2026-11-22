#!/usr/bin/env python3
"""Write Minecraft's offline UUID whitelist and operator files from .env."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path
from uuid import UUID

USERNAME = re.compile(r"^[A-Za-z0-9_]{3,16}$")


def read_env(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        result[key.strip()] = value.strip()
    return result


def offline_uuid(username: str) -> str:
    # Match Java UUID.nameUUIDFromBytes("OfflinePlayer:" + name) for offline-mode servers.
    digest = hashlib.md5(("OfflinePlayer:" + username).encode("utf-8")).digest()
    return str(UUID(bytes=digest, version=3))


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: prepare-offline-users.py .env data-directory", file=sys.stderr)
        return 2

    env_file = Path(sys.argv[1])
    data_dir = Path(sys.argv[2])
    env = read_env(env_file)
    admin = env.get("MC_OP", "")
    names = [item.strip() for item in env.get("MC_WHITELIST", admin).split(",") if item.strip()]

    if not USERNAME.fullmatch(admin):
        print("MC_OP in .env must be a 3-16 character TLauncher name (letters, numbers, underscore).", file=sys.stderr)
        return 2
    if not names:
        names = [admin]
    # Keep the exact OP spelling first; offline UUIDs are case-sensitive.
    names = [admin] + [name for name in names if name.casefold() != admin.casefold()]
    invalid = [name for name in names if not USERNAME.fullmatch(name)]
    if invalid:
        print("Invalid offline username(s) in MC_WHITELIST: " + ", ".join(invalid), file=sys.stderr)
        return 2

    # Keep the first spelling of each name and avoid duplicate UUIDs.
    unique: dict[str, str] = {}
    for name in names:
        unique.setdefault(name.casefold(), name)
    whitelist = [
        {"uuid": offline_uuid(name), "name": name}
        for name in unique.values()
    ]
    ops = [{"uuid": offline_uuid(admin), "name": admin, "level": 4, "bypassesPlayerLimit": True}]

    data_dir.mkdir(parents=True, exist_ok=True)
    for filename, payload in (("whitelist.json", whitelist), ("ops.json", ops)):
        path = data_dir / filename
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        temporary.replace(path)
    print(f"Prepared offline whitelist ({len(whitelist)} names) and OP for {admin}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
