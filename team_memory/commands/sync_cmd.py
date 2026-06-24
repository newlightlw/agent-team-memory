"""team-memory sync — 与 Gitea 远程同步(pull + push)。

不自动 add/commit(人工审核原则); 只同步已 commit 的内容。
同时提示多源(tencent-openclaw)状态, 但不改动它
(由现有 sync-remote-memory 独立管理, 符合"并存但打通")。
"""

from __future__ import annotations

from pathlib import Path

from rich.console import Console

from ..config import load_config
from ..gitutil import add_remote, run_git
from ..sources import discover_sources
from ..store import MemoryStore

__all__ = ["sync_cmd"]


def sync_cmd(
    root: Path | None = None,
    *,
    push: bool = True,
    pull: bool = True,
    console: Console | None = None,
) -> bool:
    """与 Gitea 同步; 返回是否成功。"""
    console = console or Console()
    store = MemoryStore.open(root)
    config = load_config(env_path=store.root / ".env")

    if not config.has_gitea_remote:
        console.print("[red]✗ 未配置 GITEA_REMOTE_URL[/]")
        console.print(f"  请编辑 {store.root}/.env 后重试")
        return False
    if config.is_remote_placeholder:
        console.print("[yellow]✗ GITEA_REMOTE_URL 仍是占位符(example.com)[/]")
        console.print(f"  请编辑 {store.root}/.env 填入真实 Gitea 地址")
        return False

    url = config.resolved_remote_url()
    added = add_remote(store.root, url, "origin")
    console.print(
        f"[green]✓[/] origin = {config.gitea_remote_url}" + (" (新增)" if added else "")
    )

    # pull: 首次可能无 upstream, 失败仅警告不阻断 push
    if pull:
        result = run_git(store.root, "pull", "--rebase", "origin")
        if result.returncode != 0:
            console.print(
                "[yellow]⚠ pull 未完成(可能是首次/无 upstream, 将尝试 push):[/]"
            )
            console.print(result.stderr.strip() or result.stdout.strip())
        else:
            console.print("[green]✓[/] pull --rebase 完成")

    ok = True
    if push:
        result = run_git(store.root, "push", "-u", "origin", "HEAD")
        if result.returncode != 0:
            console.print("[red]✗ push 失败:[/]")
            console.print(result.stderr.strip() or result.stdout.strip())
            ok = False
        else:
            console.print("[green]✓[/] push 完成")

    # 多源提示(不改动 tencent-openclaw)
    for source in discover_sources(config, store.root):
        if source.kind == "openclaw":
            console.print(
                f"[dim]另: tencent-openclaw 源 {source.path} "
                "由现有 sync-remote-memory 独立管理, 本命令不改动。[/]"
            )

    if ok:
        console.print("[bold green]同步完成。[/]")
    return ok
