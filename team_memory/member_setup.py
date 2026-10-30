"""Merge a separate read-only GitHub MCP into selected clients, with private backups."""

from __future__ import annotations
import json
import os
from pathlib import Path
import re
import tempfile
import tomllib
from uuid import uuid4
import yaml

NAME = "team_memory_github"


def _atomic(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(dir=path.parent, prefix=".team-memory-")
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w") as stream:
            stream.write(text)
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def configure_clients(
    root: Path,
    python: Path,
    tools: list[str],
    *,
    home: Path | None = None,
    author="member",
):
    home = home or Path.home()
    if any(t not in ("codex", "claude", "hermes", "none") for t in tools):
        raise ValueError(
            "Select codex, claude, hermes, or none; other clients use the documented manual MCP config"
        )
    if not re.fullmatch(r"[a-z0-9_]{1,32}", author):
        raise ValueError("Author must be lowercase ASCII")
    env = {
        "TEAM_MEMORY_ROOT": str(root),
        "TEAM_MEMORY_AUTHOR": author,
        "TEAM_MEMORY_OUTBOX": str(home / ".config/team-memory/outbox"),
        "TEAM_MEMORY_AUTO_SYNC": "1",
    }
    entry = {
        "command": str(python),
        "args": ["-m", "team_memory.shared_mcp"],
        "env": env,
    }
    changes = []
    for tool in dict.fromkeys(tools):
        if tool == "none":
            continue
        path = {
            "codex": home / ".codex/config.toml",
            "claude": home / ".claude.json",
            "hermes": home / ".hermes/config.yaml",
        }[tool]
        if path.is_symlink():
            raise ValueError("Client config symlink requires manual setup")
        original = path.read_text() if path.exists() else ""
        if tool == "codex":
            data = tomllib.loads(original)
            existing = data.get("mcp_servers", {}).get(NAME)
            addition = (
                "\n[mcp_servers."
                + NAME
                + "]\ncommand = "
                + json.dumps(entry["command"])
                + "\nargs = "
                + json.dumps(entry["args"])
                + "\n[mcp_servers."
                + NAME
                + ".env]\n"
                + "".join(k + " = " + json.dumps(v) + "\n" for k, v in env.items())
            )
            updated = original.rstrip() + "\n" + addition
            if existing is None:
                tomllib.loads(updated)
        elif tool == "claude":
            data = json.loads(original or "{}")
            existing = data.get("mcpServers", {}).get(NAME)
            entry_json = dict(entry, type="stdio")
            data.setdefault("mcpServers", {})[NAME] = entry_json
            updated = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
        else:
            data = yaml.safe_load(original) or {}
            existing = data.get("mcp_servers", {}).get(NAME)
            lines = original.splitlines(keepends=True)
            key = None
            for i, line in enumerate(lines):
                if re.fullmatch(r"mcp_servers:\s*(?:#.*)?\n?", line):
                    key = i
                    break
            if "mcp_servers" in data and key is None:
                raise ValueError(
                    "Inline/custom Hermes MCP mapping requires manual setup"
                )
            addition = "  " + NAME + ": " + json.dumps(entry) + "\n"
            if key is None:
                updated = original.rstrip() + "\nmcp_servers:\n" + addition
            else:
                lines.insert(key + 1, addition)
                updated = "".join(lines)
            yaml.safe_load(updated)
        if existing is not None:
            if (
                existing.get("command") != entry["command"]
                or existing.get("args") != entry["args"]
                or existing.get("env") != env
            ):
                raise ValueError(
                    "Existing " + NAME + " points elsewhere; no client files modified"
                )
            continue
        changes.append((path, original, updated, path.exists()))
    # Preflight ALL clients before any write. Backups contain existing secrets and
    # are private; return paths only. Do not write or replace unrelated MCP entries.
    backups = home / ".config/team-memory/backups" / uuid4().hex
    if changes:
        backups.mkdir(parents=True, mode=0o700)
    written = []
    try:
        for i, (path, original, updated, existed) in enumerate(changes):
            if existed:
                _atomic(backups / (str(i) + "-" + path.name), original)
            if (
                path.exists() != existed
                or (path.read_text() if path.exists() else "") != original
            ):
                raise ValueError("Client config changed concurrently")
            _atomic(path, updated)
            written.append((path, original, updated, existed))
    except Exception:
        for path, original, updated, existed in reversed(written):
            if not path.exists() or path.read_text() != updated:
                continue  # Do not overwrite a concurrent user edit during recovery.
            if existed:
                _atomic(path, original)
            else:
                path.unlink()
        raise
    return {
        "configured": [str(p) for p, *_ in changes],
        "backup_directory": str(backups) if changes else None,
        "mcp_name": NAME,
    }
