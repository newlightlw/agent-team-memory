"""
Mem0 + DeepSeek 长期记忆 demo。

用法:
    pip install "mem0ai" "chromadb" "openai"
    export DEEPSEEK_API_KEY="sk-..."
    export DASHSCOPE_API_KEY="sk-..."
    python3 test_mem0.py

可选配置:
    export DEEPSEEK_MODEL="deepseek-v4-flash"
    export DEEPSEEK_BASE_URL="https://api.deepseek.com"
    export DASHSCOPE_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"
    export QWEN_EMBEDDING_MODEL="text-embedding-v4"
    export MEM0_USER_ID="test_1"
    export MEM0_DB_PATH="./mem0_chroma_db"

说明:
    DeepSeek 官网 API 兼容 OpenAI Chat Completions 协议，用来生成回复。
    Mem0 做向量检索时还需要 embedding 模型；这里使用阿里云百炼 /
    DashScope 的 OpenAI-compatible embedding 接口。也就是说：
    DeepSeek 负责聊天，通义千问 text-embedding-v4 负责记忆向量化。
"""

from __future__ import annotations

from datetime import datetime
import os
import sys
import logging
from typing import Any

from openai import OpenAI


# 关闭 Mem0 遥测，避免 demo 启动时尝试访问 PostHog。
os.environ.setdefault("MEM0_TELEMETRY", "False")

# Mem0 的 OpenAI 适配器在检测到 OPENROUTER_API_KEY 时会优先走 OpenRouter。
# 这里显式清理，保证本 demo 只走 DeepSeek 官网接口。
os.environ.pop("OPENROUTER_API_KEY", None)
os.environ.pop("OPENROUTER_API_BASE", None)
os.environ.pop("OPENROUTER_BASE_URL", None)

# 这些 warning 对 demo 功能无影响：Chroma 不支持 BM25 混合搜索、spaCy 是可选 NLP 依赖。
logging.getLogger("mem0.memory.main").setLevel(logging.ERROR)
logging.getLogger("mem0.utils.spacy_models").setLevel(logging.ERROR)

# DeepSeek：负责普通聊天回复。
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")

# DashScope / 阿里云百炼：负责 embedding，把记忆变成向量后写入 Chroma。
DASHSCOPE_BASE_URL = os.getenv(
    "DASHSCOPE_BASE_URL",
    "https://dashscope.aliyuncs.com/compatible-mode/v1",
)
QWEN_EMBEDDING_MODEL = os.getenv("QWEN_EMBEDDING_MODEL", "text-embedding-v4")
QWEN_EMBEDDING_DIMS = os.getenv("QWEN_EMBEDDING_DIMS")

# Mem0 本地存储配置：Chroma 存向量，history_db 存对话/记忆变更历史。
MEM0_DB_PATH = os.getenv("MEM0_DB_PATH", "./mem0_chroma_db")
MEM0_HISTORY_DB_PATH = os.getenv("MEM0_HISTORY_DB_PATH", "./mem0_history.db")
MEM0_COLLECTION = os.getenv("MEM0_COLLECTION", "deepseek_mem0_demo")
DEFAULT_USER_ID = os.getenv("MEM0_USER_ID", "test_1")
MEM0_EXPORT_PATH = os.getenv("MEM0_EXPORT_PATH", "./mem0_memories.md")


def require_env(name: str) -> str:
    """读取必须存在的环境变量，缺失时给出明确错误。"""
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def import_mem0_memory():
    """延迟导入 Mem0，让缺依赖时的错误更友好。"""
    try:
        from mem0 import Memory
    except ImportError as exc:
        raise RuntimeError(
            "Missing dependency: mem0ai. Install it with:\n"
            "  pip install mem0ai chromadb"
        ) from exc

    return Memory


def build_memory_config(deepseek_api_key: str, dashscope_api_key: str) -> dict[str, Any]:
    """
    构造 Mem0 本地配置。

    Mem0 的 llm/embedder 都使用 provider="openai"，这是因为 DeepSeek 和
    DashScope 都提供 OpenAI-compatible API。真正请求到哪里由各自的
    openai_base_url 和 api_key 决定。
    """
    config: dict[str, Any] = {
        # LLM：用 DeepSeek 官网 API 对用户对话做回复，也用于 Mem0 的记忆抽取。
        "llm": {
            "provider": "openai",
            "config": {
                "api_key": deepseek_api_key,
                "openai_base_url": DEEPSEEK_BASE_URL,
                "model": DEEPSEEK_MODEL,
                "temperature": 0.2,
                "max_tokens": 1200,
            },
        },
        # 向量库：Chroma 会在本地目录里生成 sqlite/parquet 等文件，重启后仍保留记忆。
        "vector_store": {
            "provider": "chroma",
            "config": {
                "collection_name": MEM0_COLLECTION,
                "path": MEM0_DB_PATH,
            },
        },
        "history_db_path": MEM0_HISTORY_DB_PATH,
        # Embedding：用通义千问 / DashScope 的 text-embedding-v4 生成记忆向量。
        "embedder": {
            "provider": "openai",
            "config": {
                "api_key": dashscope_api_key,
                "openai_base_url": DASHSCOPE_BASE_URL,
                "model": QWEN_EMBEDDING_MODEL,
            },
        },
    }

    # 部分 embedding 模型支持指定输出维度；不设置时使用服务端默认维度。
    if QWEN_EMBEDDING_DIMS:
        config["embedder"]["config"]["embedding_dims"] = int(QWEN_EMBEDDING_DIMS)

    return config


def normalize_memories(search_result: Any) -> list[str]:
    """
    把 Mem0 search 的返回值统一整理成字符串列表。

    不同 Mem0 版本/托管形态的返回结构略有差异，这里兼容：
    {"results": [{"memory": "..."}]} 和 [{"memory": "..."}]。
    """
    if isinstance(search_result, dict):
        items = search_result.get("results", [])
    else:
        items = search_result or []

    memories: list[str] = []
    for item in items:
        if isinstance(item, dict) and item.get("memory"):
            memories.append(str(item["memory"]))
        elif isinstance(item, str):
            memories.append(item)
    return memories


def extract_results(result: Any) -> list[dict[str, Any]]:
    """从 Mem0 的返回值中取出 results，供测试命令打印使用。"""
    if isinstance(result, dict):
        items = result.get("results", [])
    else:
        items = result or []
    return [item for item in items if isinstance(item, dict)]


def print_memory_result(result: Any) -> None:
    """把记忆列表打印成人类可读格式。"""
    items = extract_results(result)
    if not items:
        print("(no memories)")
        return

    for index, item in enumerate(items, start=1):
        memory = item.get("memory") or item.get("text") or item
        score = item.get("score")
        memory_id = item.get("id")
        suffix = []
        if score is not None:
            suffix.append(f"score={score:.4f}" if isinstance(score, float) else f"score={score}")
        if memory_id:
            suffix.append(f"id={memory_id}")
        suffix_text = f" ({', '.join(suffix)})" if suffix else ""
        print(f"{index}. {memory}{suffix_text}")


def markdown_escape(value: Any) -> str:
    """把内容转成 Markdown 表格里安全显示的一行文本。"""
    text = "" if value is None else str(value)
    return text.replace("|", "\\|").replace("\n", "<br>")


def format_memory_markdown(
    result: Any,
    user_id: str,
    export_path: str = MEM0_EXPORT_PATH,
) -> str:
    """把当前用户的记忆整理成方便查看的 Markdown 文本。"""
    items = extract_results(result)
    exported_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "# Mem0 本地记忆",
        "",
        f"- user_id: `{user_id}`",
        f"- collection: `{MEM0_COLLECTION}`",
        f"- vector_db: `{MEM0_DB_PATH}`",
        f"- history_db: `{MEM0_HISTORY_DB_PATH}`",
        f"- exported_at: `{exported_at}`",
        f"- export_path: `{export_path}`",
        "",
    ]

    if not items:
        lines.append("(no memories)")
        lines.append("")
        return "\n".join(lines)

    lines.extend(
        [
            "| # | memory | score | id | event | metadata |",
            "|---:|---|---:|---|---|---|",
        ]
    )
    for index, item in enumerate(items, start=1):
        memory = item.get("memory") or item.get("text") or ""
        metadata = item.get("metadata") or {}
        lines.append(
            "| "
            f"{index} | "
            f"{markdown_escape(memory)} | "
            f"{markdown_escape(item.get('score', ''))} | "
            f"{markdown_escape(item.get('id', ''))} | "
            f"{markdown_escape(item.get('event', ''))} | "
            f"{markdown_escape(metadata)} |"
        )
    lines.append("")
    return "\n".join(lines)


class Mem0DeepSeekDemo:
    def __init__(self, deepseek_api_key: str, dashscope_api_key: str) -> None:
        # 某些 Mem0 版本还会从 OPENAI_* 环境变量读取 LLM 配置，这里同步写入。
        os.environ["OPENAI_API_KEY"] = deepseek_api_key
        os.environ["OPENAI_BASE_URL"] = DEEPSEEK_BASE_URL

        Memory = import_mem0_memory()
        self.memory = Memory.from_config(
            build_memory_config(deepseek_api_key, dashscope_api_key)
        )
        self.client = OpenAI(api_key=deepseek_api_key, base_url=DEEPSEEK_BASE_URL)

    def chat_with_memories(self, message: str, user_id: str = DEFAULT_USER_ID) -> str:
        # 1. 先从 Mem0 检索当前用户相关的长期记忆。
        relevant_memories = self.memory.search(
            query=message,
            filters={"user_id": user_id},
            top_k=5,
        )
        memories = normalize_memories(relevant_memories)
        memories_text = "\n".join(f"- {memory}" for memory in memories)
        if not memories_text:
            memories_text = "No memories found."

        # 2. 把检索到的记忆塞进 system prompt，让 DeepSeek 带着记忆回答。
        system_prompt = (
            "You are a helpful AI assistant with long-term memory.\n"
            "Answer the user based on the current query and the memories below.\n\n"
            f"User Memories:\n{memories_text}"
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message},
        ]

        # 3. 调用 DeepSeek 官网 OpenAI-compatible Chat Completions。
        response = self.client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=messages,
            stream=False,
        )
        assistant_response = response.choices[0].message.content or ""

        # 4. 把本轮 user/assistant 对话交给 Mem0，Mem0 会抽取事实并写入向量库。
        self.memory.add(
            [
                {"role": "user", "content": message},
                {"role": "assistant", "content": assistant_response},
            ],
            user_id=user_id,
        )

        return assistant_response

    def list_memories(self, user_id: str = DEFAULT_USER_ID, top_k: int = 20) -> Any:
        """列出某个 user_id 下的记忆。"""
        return self.memory.get_all(filters={"user_id": user_id}, top_k=top_k)

    def search_memories(
        self,
        query: str,
        user_id: str = DEFAULT_USER_ID,
        top_k: int = 10,
    ) -> Any:
        """直接搜索记忆，不经过 DeepSeek 聊天。"""
        return self.memory.search(
            query=query,
            filters={"user_id": user_id},
            top_k=top_k,
        )

    def remember(self, text: str, user_id: str = DEFAULT_USER_ID) -> Any:
        """直接写入一条测试记忆，方便验证 Mem0 是否工作。"""
        return self.memory.add(text, user_id=user_id, infer=True)

    def export_memories(
        self,
        user_id: str = DEFAULT_USER_ID,
        export_path: str = MEM0_EXPORT_PATH,
        top_k: int = 1000,
    ) -> str:
        """把当前用户的记忆导出成 Markdown 文件，方便本地直接查看。"""
        result = self.list_memories(user_id=user_id, top_k=top_k)
        content = format_memory_markdown(result, user_id=user_id, export_path=export_path)
        with open(export_path, "w", encoding="utf-8") as file:
            file.write(content)
        return export_path


def print_help() -> None:
    """打印交互式测试命令说明。"""
    print(
        "Commands:\n"
        "  /help                 Show this help\n"
        "  /memories [n]         List latest memories for current user\n"
        "  /search <query>       Search memories directly\n"
        "  /remember <text>      Add a test memory without chatting\n"
        "  /export [n]           Export memories to local Markdown\n"
        "  /exit                 Quit\n"
        "\n"
        "Anything else is sent as a normal chat message."
    )


def parse_limit(value: str | None, default: int) -> int:
    """解析 /memories 后面的数量参数，非法时回退默认值。"""
    if not value:
        return default
    try:
        return max(1, int(value))
    except ValueError:
        return default


def main() -> int:
    # 启动时检查两个 key：DeepSeek 用于聊天，DashScope 用于 embedding。
    try:
        deepseek_api_key = require_env("DEEPSEEK_API_KEY")
        dashscope_api_key = require_env("DASHSCOPE_API_KEY")
        demo = Mem0DeepSeekDemo(deepseek_api_key, dashscope_api_key)
    except Exception as exc:
        print(f"Startup failed: {exc}", file=sys.stderr)
        return 1

    print("Mem0 + DeepSeek demo. Type 'exit' to quit.")
    print(
        f"user_id={DEFAULT_USER_ID}, chat_model={DEEPSEEK_MODEL}, "
        f"embed_model={QWEN_EMBEDDING_MODEL}, db={MEM0_DB_PATH}"
    )
    print(f"memory_export={MEM0_EXPORT_PATH}")
    print("Type /help for memory test commands.")
    try:
        print(f"Exported memories to {demo.export_memories(DEFAULT_USER_ID)}")
    except Exception as exc:
        print(f"Initial memory export failed: {exc}", file=sys.stderr)

    while True:
        user_input = input("\nYou: ").strip()
        if user_input.lower() in {"exit", "quit", "q", "/exit", "/quit", "/q"}:
            print("Goodbye!")
            return 0
        if not user_input:
            continue

        try:
            # 以下斜杠命令是测试工具；普通文本会走 chat_with_memories。
            if user_input == "/help":
                print_help()
                continue

            if user_input.startswith("/memories"):
                _, _, raw_limit = user_input.partition(" ")
                result = demo.list_memories(
                    user_id=DEFAULT_USER_ID,
                    top_k=parse_limit(raw_limit.strip(), 20),
                )
                print_memory_result(result)
                continue

            if user_input.startswith("/export"):
                _, _, raw_limit = user_input.partition(" ")
                limit = parse_limit(raw_limit.strip(), 1000)
                export_path = demo.export_memories(
                    user_id=DEFAULT_USER_ID,
                    top_k=limit,
                )
                print(f"Exported memories to {export_path}")
                continue

            if user_input.startswith("/search "):
                query = user_input.removeprefix("/search ").strip()
                if not query:
                    print("Usage: /search <query>")
                    continue
                print_memory_result(demo.search_memories(query, user_id=DEFAULT_USER_ID))
                continue

            if user_input.startswith("/remember "):
                text = user_input.removeprefix("/remember ").strip()
                if not text:
                    print("Usage: /remember <text>")
                    continue
                result = demo.remember(text, user_id=DEFAULT_USER_ID)
                print_memory_result(result)
                print(f"Exported memories to {demo.export_memories(DEFAULT_USER_ID)}")
                continue

            answer = demo.chat_with_memories(user_input, user_id=DEFAULT_USER_ID)
            print(f"Exported memories to {demo.export_memories(DEFAULT_USER_ID)}")
        except Exception as exc:
            print(f"AI call failed: {exc}", file=sys.stderr)
            return 1

        print(f"AI: {answer}")


if __name__ == "__main__":
    raise SystemExit(main())
