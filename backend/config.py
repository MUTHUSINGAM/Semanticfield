from pathlib import Path
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ROOT_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "SemanticShield AI"
    app_env: str = "development"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000
    frontend_url: str = "http://localhost:5173"
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    enterprise_name: str = "Singam Technologies Pvt Ltd"
    demo_mode: bool = True

    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "semanticshield"

    jwt_secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60
    jwt_refresh_token_expire_days: int = 7

    admin_email: str = "admin@singam.com"
    admin_password: str = "Admin@123"
    security_officer_email: str = "security@singam.com"
    employee_email: str = "employee@singam.com"
    auditor_email: str = "auditor@singam.com"

    llm_provider: str = "openai"
    openai_api_key: str = ""
    openai_model: str = "gpt-4.1"
    openai_verification_model: str = "gpt-4.1"

    embedding_provider: str = "openai"
    openai_embedding_model: str = "text-embedding-3-small"

    lancedb_path: str = "./lancedb"
    lancedb_table_name: str = "enterprise_embeddings"
    similarity_threshold: float = 0.75
    top_k_matches: int = 5

    risk_low_action: str = "allow"
    risk_medium_action: str = "mask"
    risk_high_action: str = "block"
    risk_critical_action: str = "human_review"

    chunk_size: int = 512
    chunk_overlap: int = 64

    use_mock_enterprise_data: bool = True
    enterprise_data_path: str = "./data/enterprise"

    slack_bot_token: str = ""
    slack_app_token: str = ""
    clickup_api_token: str = ""
    clickup_workspace_id: str = ""
    notion_api_key: str = ""
    notion_database_id: str = ""
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = ""

    mcp_sync_interval_seconds: int = 300
    mcp_realtime_sync_enabled: bool = True

    log_level: str = "INFO"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def lancedb_abs_path(self) -> Path:
        path = Path(self.lancedb_path)
        if not path.is_absolute():
            path = ROOT_DIR / path
        return path

    @property
    def enterprise_data_abs_path(self) -> Path:
        path = Path(self.enterprise_data_path)
        if not path.is_absolute():
            path = ROOT_DIR / path
        return path

    @property
    def has_openai_key(self) -> bool:
        key = self.openai_api_key.strip()
        return bool(key) and key != "sk-your-openai-api-key" and key.startswith("sk-")


@lru_cache
def get_settings() -> Settings:
    return Settings()
