from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    host: str = "127.0.0.1"
    port: int = 3022
    staging_db_path: str = "~/.cache/northstar/staging.db"
    research_agent_url: str = "http://127.0.0.1:8099"
    log_level: str = "INFO"

    model_config = {"env_prefix": "", "case_sensitive": False}


settings = Settings()
