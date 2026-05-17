from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    host: str = "127.0.0.1"
    port: int = 3010
    database_url: str = "postgresql+asyncpg://northstar:northstar@127.0.0.1:5432/northstar"
    neo4j_uri: str = "bolt://127.0.0.1:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "northstar"
    chroma_persist_dir: str = "~/.cache/northstar/chromadb"
    research_agent_url: str = "http://127.0.0.1:8099"
    force_graph_extraction: bool = False
    enable_destructive_cleanup: bool = False
    log_level: str = "INFO"

    model_config = {"env_prefix": "", "case_sensitive": False}


settings = Settings()
