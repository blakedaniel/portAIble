"""Application configuration — env-driven AppSettings with workspace-outside-repo guard."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import dotenv

dotenv.load_dotenv()


PROJECT_ROOT = Path(__file__).resolve().parents[3]

_DEFAULT_WORKSPACE_DIR = "/tmp/portaible-workspace"


def _resolve_workspace_dir(raw: str) -> str:
    """Return an absolute workspace path, rejecting values inside the repo.

    Mirrors local-chat-agent's guard: the workspace must live outside the repo so
    pipeline writes (extracted source, generated artifacts, the SQLite DB, etc.)
    cannot leak into source or submodule trees.
    """
    resolved = Path(os.path.abspath(raw))
    try:
        resolved.relative_to(PROJECT_ROOT)
    except ValueError:
        return str(resolved)
    raise ValueError(
        f"WORKSPACE_DIR must resolve outside the repository ({PROJECT_ROOT}); "
        f"got {resolved}. Pick a path under /tmp or another location outside the repo."
    )


def _default_database_url(workspace: str) -> str:
    return f"sqlite+aiosqlite:///{Path(workspace).resolve() / 'portaible.db'}"


def _resolve_prompt_bank_dir(raw: str) -> str:
    p = Path(raw)
    if not p.is_absolute():
        p = (PROJECT_ROOT / p).resolve()
    return str(p)


@dataclass
class AppSettings:
    # Server
    host: str = "0.0.0.0"
    port: int = 8001
    log_level: str = "INFO"

    # Workspace + DB
    workspace_dir: str = _DEFAULT_WORKSPACE_DIR
    database_url: str = ""

    # Ollama / DSPy
    ollama_url: str = "http://localhost:11434"
    ollama_api_key: str = "ollama"
    source_analyzer_model: str = "gemma3:27b"
    destination_suggest_model: str = ""
    design_decisions_model: str = ""
    llm_timeout: int = 180
    llm_max_retries: int = 3
    num_ctx: int = 32768

    # Source extraction / analyzer caps
    github_clone_depth: int = 1
    analyzer_max_files: int = 200
    analyzer_max_file_bytes: int = 20000

    # AI Pipeline (local-chat-agent)
    ai_pipeline_url: str = "http://localhost:8000"
    ai_pipeline_timeout: int = 600
    ai_pipeline_poll_interval_seconds: float = 2.0

    # Prompt bank
    prompt_bank_dir: str = str(PROJECT_ROOT / "prompt-bank")

    # CORS — comma-separated list; Nuxt may pick an alternate port if 3000 is taken
    frontend_origins: tuple[str, ...] = ("http://localhost:3000", "http://localhost:3001",
                                          "http://localhost:3002")

    # File handling — same conservative set as local-chat-agent
    allowed_extensions: frozenset[str] = field(default_factory=lambda: frozenset({
        ".py", ".js", ".ts", ".tsx", ".jsx", ".html", ".css",
        ".vue", ".svelte",
        ".scss", ".sass", ".less",
        ".java", ".kt", ".cpp", ".c", ".h", ".rs", ".go", ".php", ".rb", ".cs",
        ".json", ".yaml", ".yml", ".toml", ".sql", ".md", ".txt",
        ".gradle", ".xml",
    }))

    @classmethod
    def from_env(cls) -> "AppSettings":
        workspace = _resolve_workspace_dir(os.getenv("WORKSPACE_DIR", cls.workspace_dir))
        database_url = os.getenv("DATABASE_URL", "").strip() or _default_database_url(workspace)
        prompt_bank_dir = _resolve_prompt_bank_dir(os.getenv("PROMPT_BANK_DIR", cls.prompt_bank_dir))
        return cls(
            host=os.getenv("APP_HOST", cls.host),
            port=int(os.getenv("APP_PORT", cls.port)),
            log_level=os.getenv("LOG_LEVEL", cls.log_level),
            workspace_dir=workspace,
            database_url=database_url,
            ollama_url=os.getenv("OLLAMA_URL", cls.ollama_url),
            ollama_api_key=os.getenv("OLLAMA_API_KEY", cls.ollama_api_key),
            source_analyzer_model=os.getenv("SOURCE_ANALYZER_MODEL", cls.source_analyzer_model),
            destination_suggest_model=os.getenv("DESTINATION_SUGGEST_MODEL", "")
                or os.getenv("SOURCE_ANALYZER_MODEL", cls.source_analyzer_model),
            design_decisions_model=os.getenv("DESIGN_DECISIONS_MODEL", "")
                or os.getenv("SOURCE_ANALYZER_MODEL", cls.source_analyzer_model),
            llm_timeout=int(os.getenv("LLM_TIMEOUT", cls.llm_timeout)),
            llm_max_retries=int(os.getenv("LLM_MAX_RETRIES", cls.llm_max_retries)),
            num_ctx=int(os.getenv("NUM_CTX", cls.num_ctx)),
            github_clone_depth=int(os.getenv("GITHUB_CLONE_DEPTH", cls.github_clone_depth)),
            analyzer_max_files=int(os.getenv("ANALYZER_MAX_FILES", cls.analyzer_max_files)),
            analyzer_max_file_bytes=int(os.getenv("ANALYZER_MAX_FILE_BYTES", cls.analyzer_max_file_bytes)),
            ai_pipeline_url=os.getenv("AI_PIPELINE_URL", cls.ai_pipeline_url).rstrip("/"),
            ai_pipeline_timeout=int(os.getenv("AI_PIPELINE_TIMEOUT", cls.ai_pipeline_timeout)),
            ai_pipeline_poll_interval_seconds=float(
                os.getenv("AI_PIPELINE_POLL_INTERVAL_SECONDS", cls.ai_pipeline_poll_interval_seconds)
            ),
            prompt_bank_dir=prompt_bank_dir,
            frontend_origins=tuple(
                o.strip() for o in os.getenv(
                    "FRONTEND_ORIGIN",
                    ",".join(cls.frontend_origins),
                ).split(",") if o.strip()
            ),
        )

    def session_dir(self, session_id: str) -> Path:
        return Path(self.workspace_dir) / "sessions" / session_id


settings = AppSettings.from_env()
