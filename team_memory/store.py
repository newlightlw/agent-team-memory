"""存储层 — 记忆仓库根定位 + 记忆条目 CRUD。

记忆仓库根由标记文件 `.team-memory.yml` 标识(init 命令创建)。
记忆文件名约定: 以 `mem-` 开头, 如 `mem-20260623-001-slug.md`;
不以 `mem-` 开头的 .md(模板、_index、README)会被自动跳过。
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .models import (
    TYPE_DIR,
    MemoryEntry,
    MemoryParseError,
    MemoryType,
    format_memory_id,
    memory_id_date,
    parse_memory,
    serialize_memory,
    today_compact,
)

__all__ = [
    "MARKER_FILE",
    "NotAMemoryRepoError",
    "find_memory_root",
    "MemoryStore",
]

# 记忆仓库根标记文件
MARKER_FILE = ".team-memory.yml"


class NotAMemoryRepoError(FileNotFoundError):
    """当前目录不在一个记忆仓库内(找不到 .team-memory.yml)。"""


def find_memory_root(start: Path | None = None) -> Path | None:
    """从 start(默认 cwd) 向上查找记忆仓库根; 找不到返回 None。"""
    current = (start or Path.cwd()).resolve()
    for parent in [current, *current.parents]:
        if (parent / MARKER_FILE).exists():
            return parent
    return None


def _slugify(text: str) -> str:
    """把标题转成文件名安全的 slug; 中文会被过滤掉(仅保留 ascii)。"""
    slug = re.sub(r"[^a-zA-Z0-9\s-]", "", text).strip().lower()
    slug = re.sub(r"[\s-]+", "-", slug).strip("-")
    return slug


def _filename_for(entry: MemoryEntry, slug: str | None = None) -> str:
    """生成记忆文件名: mem-YYYYMMDD-NNN[-slug].md。"""
    resolved = (slug if slug is not None else _slugify(entry.title)).strip()
    return f"{entry.id}-{resolved}.md" if resolved else f"{entry.id}.md"


@dataclass(frozen=True)
class MemoryStore:
    """对一个记忆仓库的只读/写入访问器。不可变; 持有 root 路径。"""

    root: Path

    @classmethod
    def open(cls, root: Path | None = None) -> MemoryStore:
        """打开记忆仓库; root 为 None 时自动定位。

        Raises:
            NotAMemoryRepoError: 找不到记忆仓库标记。
        """
        if root is not None:
            resolved = Path(root).resolve()
        else:
            found = find_memory_root()
            if found is None:
                raise NotAMemoryRepoError(
                    f"当前目录不在记忆仓库内(向上未找到 {MARKER_FILE})。"
                    "请先运行 `team-memory init`。"
                )
            resolved = found
        if not (resolved / MARKER_FILE).exists():
            raise NotAMemoryRepoError(
                f"{resolved} 不是记忆仓库根(缺少 {MARKER_FILE})。"
            )
        return cls(root=resolved)

    # ---- 路径辅助 ----

    def memory_dir(self) -> Path:
        return self.root / "memory"

    def dir_for(self, type_: MemoryType | str) -> Path:
        key = type_.value if isinstance(type_, MemoryType) else type_
        if key not in TYPE_DIR:
            raise ValueError(f"未知的记忆类型: {key!r}")
        return self.memory_dir() / TYPE_DIR[key]

    # ---- 查询 ----

    def list_entries(self, type_filter: str | None = None) -> list[MemoryEntry]:
        """列出记忆条目。type_filter 可限定单类; 解析失败的文件被跳过。"""
        if type_filter:
            dirs = [self.dir_for(type_filter)]
        else:
            dirs = [self.memory_dir() / name for name in TYPE_DIR.values()]

        entries: list[MemoryEntry] = []
        for directory in dirs:
            if not directory.exists():
                continue
            for md in sorted(directory.glob("*.md")):
                # 按内容判断: 能解析为合法 frontmatter 的才算记忆;
                # 模板/README/_index 等无 frontmatter 的会被自动跳过。
                try:
                    entries.append(parse_memory(md.read_text(encoding="utf-8")))
                except MemoryParseError:
                    continue
        return entries

    def get_entry(self, memory_id: str) -> MemoryEntry | None:
        """按 id 查找记忆; 不存在返回 None。"""
        for entry in self.list_entries():
            if entry.id == memory_id:
                return entry
        return None

    def find_file(self, memory_id: str) -> Path | None:
        """按 id 查找记忆所在文件路径(按 frontmatter 内容匹配, 不依赖文件名)。"""
        for md in self.memory_dir().rglob("*.md"):
            try:
                entry = parse_memory(md.read_text(encoding="utf-8"))
            except MemoryParseError:
                continue
            if entry.id == memory_id:
                return md
        return None

    def next_id(self, date_compact: str | None = None) -> str:
        """生成下一个可用 id: 取指定日期当天已有最大序号 + 1。"""
        day = date_compact or today_compact()
        max_seq = 0
        for entry in self.list_entries():
            if memory_id_date(entry.id) == day:
                try:
                    seq = int(entry.id.rsplit("-", 1)[-1])
                    max_seq = max(max_seq, seq)
                except ValueError:
                    continue
        return format_memory_id(day, max_seq + 1)

    # ---- 写入 ----

    def save_entry(self, entry: MemoryEntry, slug: str | None = None) -> Path:
        """把记忆写入对应类型目录; 返回写入路径。"""
        target_dir = self.dir_for(entry.type)
        target_dir.mkdir(parents=True, exist_ok=True)
        path = target_dir / _filename_for(entry, slug)
        path.write_text(serialize_memory(entry), encoding="utf-8")
        return path
