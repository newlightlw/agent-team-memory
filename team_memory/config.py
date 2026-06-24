"""配置加载 — 从 .env 读取 Gitea / 团队 / 作者等配置。

优先级: 真实环境变量 > .env 文件 > dataclass 默认值。
不依赖 python-dotenv, 自带一个极简 .env 解析器。
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

__all__ = ["Config", "load_config", "parse_env_file"]

# 与 .env 中对应的键名
_ENV_KEYS = (
    "GITEA_REMOTE_URL",
    "GITEA_TOKEN",
    "TEAM_NAME",
    "DEFAULT_AUTHOR",
    "DEFAULT_MEMORY_PATH",
    "TENCENT_OPENCLAW_PATH",
)

# .env.example 占位符里的主机名, 用于判断 remote 是否仍是占位符
_PLACEHOLDER_HOST = "example.com"


def parse_env_file(path: Path) -> dict[str, str]:
    """解析 .env 文件为 dict; 文件不存在返回空 dict。

    支持: 注释(#)、空行、KEY=VALUE、首尾引号去除。
    """
    data: dict[str, str] = {}
    if not path.exists():
        return data
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        if key:
            data[key] = value
    return data


@dataclass(frozen=True)
class Config:
    """运行配置。不可变。"""

    gitea_remote_url: str = ""
    gitea_token: str = ""
    team_name: str = "我们的团队"
    default_author: str = "vayne"
    default_memory_path: str = "./memory"
    tencent_openclaw_path: str = ""

    @property
    def has_gitea_remote(self) -> bool:
        """是否配置了非空的 Gitea remote。"""
        return bool(self.gitea_remote_url.strip())

    @property
    def has_openclaw_source(self) -> bool:
        """是否配置了 tencent-openclaw 聚合源。"""
        return bool(self.tencent_openclaw_path.strip())

    @property
    def is_remote_placeholder(self) -> bool:
        """Gitea remote 是否仍是占位符(未填真实地址)。"""
        return _PLACEHOLDER_HOST in self.gitea_remote_url

    def resolved_remote_url(self) -> str:
        """返回可用于推送的 remote url。

        若是 HTTPS 且配了 token, 注入 oauth2:token 凭据; 否则原样返回(SSH 方式无需 token)。
        """
        url = self.gitea_remote_url.strip()
        token = self.gitea_token.strip()
        if token and url.startswith("https://"):
            rest = url[len("https://"):]
            netloc = rest.split("/", 1)[0]
            if "@" not in netloc:
                return f"https://oauth2:{token}@{rest}"
        return url

    @classmethod
    def from_env(cls, env_path: Path | None = None) -> Config:
        """从 .env + 环境变量加载配置。

        Args:
            env_path: .env 文件路径; None 时用 cwd/.env。
        """
        path = env_path if env_path is not None else Path.cwd() / ".env"
        merged = parse_env_file(path)
        # 真实环境变量优先级最高
        for key in _ENV_KEYS:
            env_value = os.environ.get(key)
            if env_value:
                merged[key] = env_value
        return cls(
            gitea_remote_url=merged.get("GITEA_REMOTE_URL", ""),
            gitea_token=merged.get("GITEA_TOKEN", ""),
            team_name=merged.get("TEAM_NAME", "我们的团队"),
            default_author=merged.get("DEFAULT_AUTHOR", "vayne"),
            default_memory_path=merged.get("DEFAULT_MEMORY_PATH", "./memory"),
            tencent_openclaw_path=merged.get("TENCENT_OPENCLAW_PATH", ""),
        )


def load_config(env_path: Path | None = None) -> Config:
    """加载配置的便捷函数。"""
    return Config.from_env(env_path)
