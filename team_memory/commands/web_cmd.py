"""team-memory web — 启动 Web 可视化管理服务。"""

from __future__ import annotations

from pathlib import Path

from rich.console import Console

from ..store import MemoryStore
from ..web import serve

__all__ = ["web_cmd"]


def web_cmd(
    root: Path | None = None,
    *,
    host: str = "127.0.0.1",
    port: int = 8000,
    open_browser: bool = True,
    console: Console | None = None,
) -> None:
    """启动 Web 可视化(阻塞; Ctrl+C 退出)。"""
    console = console or Console()
    store = MemoryStore.open(root)
    console.print("[bold green]team-memory web[/]")
    console.print(f"  仓库: {store.root}")
    console.print(f"  记忆: {len(store.list_entries())} 条")
    console.print(f"  地址: http://{host}:{port}")
    serve(store, host=host, port=port, open_browser=open_browser)
