from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    host: str = "127.0.0.1"
    port: int = 8099
    database_url: str = "postgresql+asyncpg://northstar:northstar@127.0.0.1:5432/northstar"
    neo4j_uri: str = "bolt://127.0.0.1:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "northstar"
    ollama_base_url: str = "http://127.0.0.1:11434"
    primary_llm_model: str = "qwen3:14b"
    fallback_llm_model: str = "llama3.1:8b"
    embedding_model: str = "nomic-embed-text"
    chroma_persist_dir: str = "~/.cache/northstar/chromadb"
    force_graph_extraction: bool = False
    enable_destructive_cleanup: bool = False
    log_level: str = "INFO"
    scraper_enabled: bool = False
    cloakbrowser_binary: str | None = None
    scraper_default_headless: bool = True
    scraper_timeout_seconds: int = 60
    scraper_max_content_length: int = 10000
    scraper_url_allowlist: list[str] | None = None

    model_config = {"env_prefix": "", "case_sensitive": False}


settings = Settings()
