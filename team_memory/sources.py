"""多源聚合 — 注册并聚合多个记忆源。

本轮支持两类源:
  - team-memory   : 本工具管理的仓库(MemoryStore 格式, 带 frontmatter)
  - tencent-openclaw: 现有 sync-remote-memory 管理的 markdown 目录(原始, 不强求 frontmatter)

设计目标: 与现有 sync-remote-memory "并存但打通" —— load 时可同时读取两类源,
而原有同步脚本保持独立运行, 不被重写或破坏。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .config import Config
from .models import MemoryEntry, MemoryParseError, parse_memory

__all__ = ["Source", "discover_sources", "iter_entries", "load_all_entries"]


@dataclass(frozen=True)
class Source:
    name: str
    path: Path
    kind: str  # "team-memory" | "openclaw"


def discover_sources(config: Config, team_root: Path | None = None) -> list[Source]:
    """发现所有已配置的记忆源。

    Args:
        config: 运行配置(从中读 tencent-openclaw 路径)。
        team_root: 当前 team-memory 仓库根(若有)。
    """
    sources: list[Source] = []
    if team_root is not None:
        sources.append(Source(name="team-memory", path=team_root, kind="team-memory"))
    if config.has_openclaw_source:
        path = Path(config.tencent_openclaw_path).expanduser()
        if path.exists():
            sources.append(
                Source(name="tencent-openclaw", path=path, kind="openclaw")
            )
    return sources


def iter_entries(source: Source) -> list[tuple[MemoryEntry, str]]:
    """读取一个源的记忆; 返回 (entry, source_name) 列表。

    能解析为带 frontmatter 记忆的纳入; 解析失败的原始 md 被跳过
    (openclaw 源不强求格式)。
    """
    entries: list[tuple[MemoryEntry, str]] = []
    if not source.path.exists():
        return entries
    for md in sorted(source.path.rglob("*.md")):
        try:
            entry = parse_memory(md.read_text(encoding="utf-8"))
        except MemoryParseError:
            continue
        entries.append((entry, source.name))
    return entries


def load_all_entries(
    config: Config, team_root: Path | None = None
) -> dict[str, list[MemoryEntry]]:
    """聚合所有源的记忆, 按源名分组返回。"""
    grouped: dict[str, list[MemoryEntry]] = {}
    for source in discover_sources(config, team_root):
        entries = iter_entries(source)
        if entries:
            grouped[source.name] = [entry for entry, _ in entries]
    return grouped
