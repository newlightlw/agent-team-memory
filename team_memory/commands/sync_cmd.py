"""team-memory sync — 与 Gitea 远程同步(pull + push), 团队版冲突处理。

改进:
  - 入口预检工作区(未提交变更警告, --force 跳过)和未完成 rebase
  - pull --rebase --autostash
  - 区分「冲突」vs「无 upstream」: 冲突时列冲突文件 + 给 abort/continue 指引, 不继续 push
不自动 add/commit(人工审核原则)。
"""

from __future__ import annotations

from pathlib import Path

from rich.console import Console

from ..config import load_config
from ..gitutil import (
    add_remote,
    conflicted_files,
    is_rebase_in_progress,
    run_git,
    working_tree_dirty,
)
from ..sources import discover_sources
from ..store import MemoryStore

__all__ = ["sync_cmd"]

_CONFLICT_KEYWORDS = (
    "conflict", "could not apply", "resolve conflict", "merge conflict",
)
_NO_UPSTREAM_KEYWORDS = (
    "no upstream", "does not have any commits yet",
    "couldn't find remote ref", "no remote-tracking branch",
)


def _matches(text: str, keywords: tuple[str, ...]) -> bool:
    lower = text.lower()
    return any(k in lower for k in keywords)


def sync_cmd(
    root: Path | None = None,
    *,
    push: bool = True,
    pull: bool = True,
    force: bool = False,
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

    # 预检 1: 未完成 rebase
    if is_rebase_in_progress(store.root):
        console.print("[red]✗ 当前有未完成的 rebase, 先解决再 sync:[/]")
        for f in conflicted_files(store.root):
            console.print(f"  冲突: {f}")
        console.print("[yellow]  git rebase --abort 放弃, 或解决后 git rebase --continue[/]")
        return False

    # 预检 2: 工作区脏
    dirty = working_tree_dirty(store.root)
    if dirty and not force:
        console.print(
            f"[yellow]⚠ 本地有 {len(dirty)} 个未提交变更, sync 前请先 commit:[/]"
        )
        for f in dirty[:10]:
            console.print(f"  {f}")
        if len(dirty) > 10:
            console.print(f"  ...等共 {len(dirty)} 个")
        console.print(
            "[dim]  (capture 不自动 commit; commit 后再 sync, 或 --force 跳过此检查)[/]"
        )
        return False

    url = config.resolved_remote_url()
    added = add_remote(store.root, url, "origin")
    console.print(
        f"[green]✓[/] origin = {config.gitea_remote_url}" + (" (新增)" if added else "")
    )

    # pull --rebase --autostash
    if pull:
        result = run_git(store.root, "pull", "--rebase", "--autostash", "origin")
        combined = result.stderr + result.stdout
        if result.returncode != 0:
            if _matches(combined, _CONFLICT_KEYWORDS) or conflicted_files(store.root):
                console.print("[red]✗ pull 时发生冲突:[/]")
                for f in conflicted_files(store.root):
                    console.print(f"  冲突: {f}")
                console.print("[yellow]解决方式:[/]")
                console.print("  1. 编辑上述文件, 删除冲突标记(<<<<<<< ======= >>>>>>>)")
                console.print("  2. git add <文件> && git rebase --continue")
                console.print("  3. 或放弃: git rebase --abort (回到 pull 前)")
                return False
            if _matches(combined, _NO_UPSTREAM_KEYWORDS):
                console.print("[dim]pull: 远端无 upstream(首次推送前正常), 继续 push[/]")
            else:
                console.print("[yellow]⚠ pull 未完成:[/]")
                console.print(combined.strip()[:500])
                console.print("[dim]  (将尝试 push; 失败请检查上方输出)[/]")

    ok = True
    if push:
        result = run_git(store.root, "push", "-u", "origin", "HEAD")
        if result.returncode != 0:
            combined = result.stderr + result.stdout
            console.print("[red]✗ push 失败:[/]")
            console.print(combined.strip()[:500])
            if "non-fast-forward" in combined.lower():
                console.print(
                    "[yellow]  远端有新提交: 先 team-memory sync pull, 再 push[/]"
                )
            ok = False
        else:
            console.print("[green]✓[/] push 完成")

    for source in discover_sources(config, store.root):
        if source.kind == "openclaw":
            console.print(
                f"[dim]另: tencent-openclaw 源 {source.path} "
                "由现有 sync-remote-memory 独立管理, 本命令不改动。[/]"
            )

    if ok:
        console.print("[bold green]同步完成。[/]")
    return ok
