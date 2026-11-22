#!/usr/bin/env python3
"""Harden AuthMe and survival-world plugin settings after their first boot."""

from __future__ import annotations

import re
import sys
from pathlib import Path


def mapping_entries(text: str) -> list[tuple[int, int, tuple[str, ...]]]:
    """Return (line index, indentation, dotted YAML path) for plain mappings."""
    entries: list[tuple[int, int, tuple[str, ...]]] = []
    stack: list[tuple[int, str]] = []
    for index, line in enumerate(text.splitlines(keepends=True)):
        raw = line.rstrip("\r\n")
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        content = raw[indent:]
        if content.startswith("- "):
            continue
        match = re.match(r"([^:]+):(.*)$", content)
        if not match:
            continue
        key = match.group(1).strip().strip("'\"")
        while stack and stack[-1][0] >= indent:
            stack.pop()
        path = tuple(name for _, name in stack) + (key,)
        entries.append((index, indent, path))
        value = match.group(2).strip()
        if not value or value.startswith("#"):
            stack.append((indent, key))
    return entries


def replace_scalar(text: str, dotted_path: str, value: str, *, add_missing: bool = False) -> str:
    target = tuple(dotted_path.split("."))
    entries = mapping_entries(text)
    matches = [entry for entry in entries if entry[2] == target]
    lines = text.splitlines(keepends=True)

    if len(matches) == 1:
        index, indent, _ = matches[0]
        raw = lines[index].rstrip("\r\n")
        newline = "\r\n" if lines[index].endswith("\r\n") else ("\n" if lines[index].endswith("\n") else "")
        colon = raw.find(":", indent)
        tail = raw[colon + 1 :]
        comment_match = re.search(r"\s+#.*$", tail)
        comment = comment_match.group(0) if comment_match else ""
        lines[index] = raw[: colon + 1] + " " + value + comment + newline
        return "".join(lines)

    if matches:
        raise ValueError(f"Duplicate YAML key path {dotted_path!r}")
    if not add_missing:
        raise ValueError(f"Missing YAML key path {dotted_path!r}")

    parent = target[:-1]
    parents = [entry for entry in entries if entry[2] == parent]
    if len(parents) != 1:
        raise ValueError(f"Expected one parent mapping for {dotted_path!r}, found {len(parents)}")
    parent_index, parent_indent, _ = parents[0]
    parent_line = lines[parent_index].rstrip("\r\n")
    if parent_line.split(":", 1)[1].strip():
        raise ValueError(f"Parent of {dotted_path!r} is not a YAML mapping")
    newline = "\r\n" if lines[parent_index].endswith("\r\n") else "\n"
    child_indent = parent_indent + 2
    insertion = " " * child_indent + target[-1] + ": " + value + newline
    lines.insert(parent_index + 1, insertion)
    return "".join(lines)


def replace_list(text: str, dotted_path: str, values: list[str]) -> str:
    target = tuple(dotted_path.split("."))
    matches = [entry for entry in mapping_entries(text) if entry[2] == target]
    if len(matches) != 1:
        raise ValueError(f"Expected one list key {dotted_path!r}, found {len(matches)}")

    lines = text.splitlines(keepends=True)
    index, indent, _ = matches[0]
    raw = lines[index].rstrip("\r\n")
    newline = "\r\n" if lines[index].endswith("\r\n") else ("\n" if lines[index].endswith("\n") else "")
    lines[index] = raw[: raw.find(":", indent) + 1] + newline

    end = index + 1
    while end < len(lines):
        candidate = lines[end].rstrip("\r\n")
        if not candidate.strip():
            break
        child_indent = len(candidate) - len(candidate.lstrip(" "))
        if child_indent <= indent or not candidate[child_indent:].startswith("- "):
            break
        end += 1

    items = [" " * (indent + 2) + "- " + item + newline for item in values]
    lines[index + 1 : end] = items
    return "".join(lines)


def update_file(path: Path, scalar_settings: dict[str, tuple[str, bool]], lists: dict[str, list[str]] | None = None) -> None:
    text = path.read_text(encoding="utf-8")
    for dotted_path, (value, add_missing) in scalar_settings.items():
        text = replace_scalar(text, dotted_path, value, add_missing=add_missing)
    for dotted_path, values in (lists or {}).items():
        text = replace_list(text, dotted_path, values)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: harden-authme.py data/plugins-directory", file=sys.stderr)
        return 2

    plugins = Path(sys.argv[1])
    update_file(
        plugins / "AuthMe" / "config.yml",
        {
            "settings.messagesLanguage": ("en", False),
            "settings.security.passwordHash": ("BCRYPT", False),
            "settings.security.minPasswordLength": ("8", False),
            "settings.security.passwordMaxLength": ("64", False),
            "settings.registration.enabled": ("true", False),
            "settings.registration.force": ("true", False),
            "settings.registration.type": ("PASSWORD", False),
            "settings.restrictions.maxRegPerIp": ("5", False),
            "settings.restrictions.teleportUnAuthedToSpawn": ("true", False),
            "settings.restrictions.allowMovement": ("false", False),
            "settings.restrictions.ProtectInventoryBeforeLogIn": ("true", False),
            "settings.restrictions.DenyTabCompleteBeforeLogin": ("true", False),
        },
    )
    update_file(
        plugins / "Multiverse-Core" / "config.yml",
        {
            "world.enforce-access": ("true", False),
            "teleport.use-finer-teleport-permissions": ("true", False),
            "teleport.teleport-intercept": ("true", False),
        },
    )
    update_file(
        plugins / "HuskHomes" / "config.yml",
        {},
        {
            "rtp.restricted_worlds": [
                "lobby",
                "lobby_nether",
                "lobby_the_end",
                "world_nether",
                "world_the_end",
                "survival_nether",
                "survival_the_end",
            ]
        },
    )
    update_file(
        plugins / "GriefPrevention" / "config.yml",
        {
            "GriefPrevention.Claims.Mode.lobby": ("Disabled", True),
            "GriefPrevention.Claims.Mode.lobby_nether": ("Disabled", True),
            "GriefPrevention.Claims.Mode.lobby_the_end": ("Disabled", True),
            "GriefPrevention.Claims.Mode.survival": ("Survival", True),
            "GriefPrevention.Claims.Mode.survival_nether": ("Survival", True),
            "GriefPrevention.Claims.Mode.survival_the_end": ("Survival", True),
        },
    )
    print("Applied AuthMe, Multiverse access, HuskHomes RTP, and claim-world settings.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError) as error:
        print(f"Plugin settings were not safely updated: {error}", file=sys.stderr)
        raise SystemExit(1)
