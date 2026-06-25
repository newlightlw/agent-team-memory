#!/usr/bin/env python3
"""新人接入团队记忆仓库 — 跨平台版(Mac / Linux / Windows)。

替代 bash 版 onboard.sh, Windows 同事直接用 python 跑。
内部用 `python -m team_memory` 调命令, 不依赖 team-memory 是否进 PATH。

用法:
  Mac/Linux: python3 scripts/onboard.py <记忆仓库git地址> <你的英文短名>
  Windows:   python  scripts/onboard.py <记忆仓库git地址> <你的英文短名>
示例:
  python scripts/onboard.py http://gitea.example.com/team/team-memory.git zhang3
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def run(cmd) -> int:
    print(f"  $ {' '.join(str(c) for c in cmd)}")
    return subprocess.run([str(c) for c in cmd]).returncode


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    repo_url = sys.argv[1]
    author = sys.argv[2] if len(sys.argv) > 2 else ""
    tool_dir = Path(__file__).resolve().parent.parent
    mem_dir = Path(os.environ.get("MEM_DIR") or (Path.home() / "team-memory"))
    py = sys.executable  # 当前 python, 跨平台

    print(f"=== 1. clone 记忆仓库到 {mem_dir} ===")
    if (mem_dir / ".git").exists():
        run(["git", "-C", mem_dir, "pull", "--rebase"])
    else:
        run(["git", "clone", repo_url, mem_dir])

    print("=== 2. 安装 team-memory 工具 ===")
    run([py, "-m", "pip", "install", "-e", tool_dir])

    print("=== 3. 配 .env(GITEA_REMOTE_URL + DEFAULT_AUTHOR) ===")
    env_file = mem_dir / ".env"
    if not env_file.exists():
        example = mem_dir / ".env.example"
        env_file.write_text(
            example.read_text(encoding="utf-8")
            if example.exists()
            else f"GITEA_REMOTE_URL={repo_url}\n",
            encoding="utf-8",
        )
    lines = env_file.read_text(encoding="utf-8").splitlines()
    out = []
    for ln in lines:
        if ln.startswith("GITEA_REMOTE_URL="):
            out.append(f"GITEA_REMOTE_URL={repo_url}")
        elif author and ln.startswith("DEFAULT_AUTHOR="):
            out.append(f"DEFAULT_AUTHOR={author}")
        else:
            out.append(ln)
    env_file.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"  GITEA_REMOTE_URL={repo_url}" + (f"\n  DEFAULT_AUTHOR={author}" if author else ""))
    print("  (按需补 GITEA_TOKEN, 或配 git credential)")

    print("=== 4. 桥接到 4 工具(装 team-memory + auto-commit skill) ===")
    run([py, "-m", "team_memory", "load", "--global", "-p", mem_dir])

    print("=== 5. 自检 ===")
    run([py, "-m", "team_memory", "doctor", "-p", mem_dir])

    print(f"\n✓ 接入完成! 记忆仓库: {mem_dir}")
    print("常用(任意平台):")
    print(f"  沉淀:  {py} -m team_memory capture '标题' -t decision --via claude -p {mem_dir}")
    print(f"  可视化: {py} -m team_memory web -p {mem_dir}")
    print(f"  同步:   {py} -m team_memory sync -p {mem_dir}")
    print("  对话中: 直接说'提交下' → auto-commit-memory 自动总结并确认提交")
    print()
    print("【可选】让 AI 工具动态读写记忆(MCP):")
    print(f"  {py} -m pip install -e '{tool_dir}[mcp]'")
    print("  配置见 docs/MCP接入.md (Claude Code/Cursor/Codex/Hermes)")


if __name__ == "__main__":
    main()
