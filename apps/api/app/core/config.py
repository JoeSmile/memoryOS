import logging
import os
from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.rag_constants import EMBEDDING_DIMENSIONS

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    app_name: str = "MemoryOS API"
    env: str = "development"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000

    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    database_url: str | None = Field(
        default="postgresql+asyncpg://memoryos:memoryos@localhost:5432/memoryos",
        description="postgresql+asyncpg://user:pass@host:5432/dbname",
    )
    db_pool_size: int = Field(
        default=5,
        description="SQLAlchemy async engine pool_size (DB_POOL_SIZE)",
    )
    db_max_overflow: int = Field(
        default=10,
        description="SQLAlchemy async engine max_overflow (DB_MAX_OVERFLOW)",
    )

    embedding_dimensions: int = Field(
        default=EMBEDDING_DIMENSIONS,
        description="pgvector column width; must match Alembic 011 vector(N)",
    )
    embedding_model: str = Field(
        default="text-embedding-v4",
        description="DashScope/OpenAI-compatible embedding model when API key is set",
    )
    embedding_api_base: str | None = Field(
        default=None,
        validation_alias="EMBEDDING_BASE_URL",
        description="OpenAI-compatible embedding API base; falls back to OPENAI_BASE_URL when unset",
    )

    rag_chat_enabled: bool = Field(
        default=True,
        description="Inject knowledge retrieval before chat generation (RAG_CHAT_ENABLED)",
    )
    rag_chat_top_k: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Max chunks passed to RAG prompt (RAG_CHAT_TOP_K)",
    )
    rag_chat_min_score: float = Field(
        default=0.35,
        ge=0.0,
        le=1.0,
        description="Min similarity score (1 - cosine distance) to include a chunk (RAG_CHAT_MIN_SCORE)",
    )
    rag_chat_collection: str | None = Field(
        default=None,
        description="Optional collection filter; unset searches all ingested collections (RAG_CHAT_COLLECTION)",
    )

    redis_url: str | None = Field(
        default=None,
        description="redis://host:6379/0 — leave unset or empty to disable cache",
    )

    conversation_list_cache_ttl: int = Field(
        default=300,
        description="seconds for memoryos:conversations:user:{id}",
    )

    stream_cache_ttl: int = Field(
        default=3600,
        description="seconds for memoryos:stream:{conversation_id}:{stream_id}",
    )

    jwt_secret: str | None = Field(
        default=None,
        description="HS256 signing secret — required for auth endpoints",
    )
    jwt_algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=60)
    password_min_length: int = Field(default=8)
    password_max_length: int = Field(default=128)

    chat_max_content_chars: int = Field(
        default=200,
        ge=1,
        le=100_000,
        description="Max user message length for chat and demo-turn (CHAT_MAX_CONTENT_CHARS); demo default 200",
    )
    prompt_injection_filter_enabled: bool = Field(
        default=True,
        description="Heuristic user-input injection filter (PROMPT_INJECTION_FILTER_ENABLED)",
    )

    openai_api_key: str | None = Field(
        default=None,
        description="OpenAI API key — unset enables mock LLM in ep02-langgraph",
    )
    openai_model: str = Field(
        default="qwen-turbo",
        description="ChatOpenAI model name when openai_api_key is set",
    )
    openai_api_base: str | None = Field(
        default="https://dashscope.aliyuncs.com/compatible-mode/v1",
        validation_alias="OPENAI_BASE_URL",
        description="OpenAI-compatible API base (DashScope for qwen-turbo)",
    )

    langsmith_tracing: bool = Field(
        default=False,
        description="Enable LangSmith tracing (LANGSMITH_TRACING)",
    )
    langsmith_api_key: str | None = Field(
        default=None,
        description="LangSmith API key (LANGSMITH_API_KEY)",
    )
    langsmith_project: str = Field(
        default="memoryOS-dev",
        description="LangSmith project name (LANGSMITH_PROJECT)",
    )
    langsmith_endpoint: str = Field(
        default="https://api.smith.langchain.com",
        description="LangSmith API endpoint (LANGSMITH_ENDPOINT)",
    )

    agent_tools_enabled: bool = Field(
        default=True,
        description="Enable unified ReAct tool loop (AGENT_TOOLS_ENABLED)",
    )
    agent_max_iterations: int = Field(
        default=5,
        ge=1,
        le=20,
        description="LangGraph recursion_limit for tool loop (AGENT_MAX_ITERATIONS)",
    )
    agent_tool_timeout_seconds: float = Field(
        default=10.0,
        gt=0.0,
        le=120.0,
        description="Per-tool execution timeout seconds (AGENT_TOOL_TIMEOUT_SECONDS)",
    )
    tavily_api_key: str | None = Field(
        default=None,
        description="Tavily API key — unset uses mock web search (TAVILY_API_KEY)",
    )
    tavily_max_results: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Max Tavily results returned to the model (TAVILY_MAX_RESULTS)",
    )

    memory_enabled: bool = Field(
        default=True,
        description="Enable memory trim, summary, and extract (MEMORY_ENABLED)",
    )
    memory_short_term_enabled: bool = Field(
        default=True,
        description="Enable short-term message trimming in graph (MEMORY_SHORT_TERM_ENABLED)",
    )
    memory_long_term_enabled: bool = Field(
        default=True,
        description="Enable long-term memories table and extract (MEMORY_LONG_TERM_ENABLED)",
    )
    memory_long_term_top_k: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Max long-term memory snippets retrieved per turn (MEMORY_LONG_TERM_TOP_K)",
    )
    memory_min_score: float = Field(
        default=0.35,
        ge=0.0,
        le=1.0,
        description="Min cosine similarity for injecting a memory snippet (MEMORY_MIN_SCORE)",
    )
    memory_prune_threshold: float = Field(
        default=0.1,
        ge=0.0,
        le=1.0,
        description="Delete memories below this importance during extract prune (MEMORY_PRUNE_THRESHOLD)",
    )
    max_context_tokens: int = Field(
        default=8192,
        ge=512,
        le=128_000,
        description="Max input context tokens per LLM turn (MAX_CONTEXT_TOKENS)",
    )
    reserve_for_reply: int = Field(
        default=1024,
        ge=128,
        le=32_000,
        description="Tokens reserved for assistant reply (RESERVE_FOR_REPLY)",
    )
    summary_trigger_tokens: int = Field(
        default=4096,
        ge=512,
        le=128_000,
        description="First summary when full history exceeds this (SUMMARY_TRIGGER_TOKENS)",
    )
    summary_increment_tokens: int = Field(
        default=1024,
        ge=128,
        le=32_000,
        description="Min new message tokens since last summary for rolling update (SUMMARY_INCREMENT_TOKENS)",
    )
    summary_cooldown_seconds: int = Field(
        default=300,
        ge=0,
        le=86_400,
        description="Min seconds between rolling summary updates (SUMMARY_COOLDOWN_SECONDS)",
    )

    @field_validator("rag_chat_collection", mode="before")
    @classmethod
    def _blank_rag_chat_collection_as_none(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def use_mock_llm(self) -> bool:
        return not (self.openai_api_key and self.openai_api_key.strip())

    @property
    def use_mock_embedding(self) -> bool:
        """Same gate as LLM: no OPENAI_API_KEY → deterministic mock vectors."""
        return self.use_mock_llm

    @property
    def use_mock_tavily(self) -> bool:
        return not (self.tavily_api_key and self.tavily_api_key.strip())


def _sync_llm_observability_env(s: Settings) -> None:
    """Expose .env values to LangChain / LangSmith SDKs (read os.environ)."""
    if s.openai_api_key:
        os.environ["OPENAI_API_KEY"] = s.openai_api_key
    if s.openai_model:
        os.environ["OPENAI_MODEL"] = s.openai_model
    if s.openai_api_base:
        os.environ["OPENAI_BASE_URL"] = s.openai_api_base
    os.environ["LANGSMITH_TRACING"] = "true" if s.langsmith_tracing else "false"
    if s.langsmith_api_key:
        os.environ["LANGSMITH_API_KEY"] = s.langsmith_api_key
    os.environ["LANGSMITH_PROJECT"] = s.langsmith_project
    os.environ["LANGSMITH_ENDPOINT"] = s.langsmith_endpoint


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    _sync_llm_observability_env(s)
    if not s.database_url:
        logger.warning(
            "DATABASE_URL is not set; DB features disabled until configured "
            "(see apps/api/.env.example, run pnpm db:up)."
        )
    if not s.redis_url:
        logger.warning(
            "REDIS_URL is not set; cache features disabled "
            "(see apps/api/.env.example)."
        )
    if not s.jwt_secret:
        logger.warning(
            "JWT_SECRET is not set; auth endpoints disabled until configured "
            "(see apps/api/.env.example)."
        )
    if s.use_mock_llm:
        logger.info(
            "OPENAI_API_KEY is not set; chat graph and embeddings use mock (CI/harness)."
        )
    return s


settings = get_settings()
