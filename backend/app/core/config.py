from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central application configuration.

    All sensitive/runtime configuration comes from environment variables.
    Never hard-code secrets inside the source code.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---------------------------------------------------------
    # APPLICATION
    # ---------------------------------------------------------

    app_name: str = "ASKLY AI Learning Platform"
    app_version: str = "3.0.0"
    environment: str = "development"
    debug: bool = False

    # ---------------------------------------------------------
    # DATABASE
    # ---------------------------------------------------------

    mongodb_uri: str = Field(
        ...,
        description="MongoDB connection string",
    )

    mongodb_database: str = "askly"

    # ---------------------------------------------------------
    # SECURITY
    # ---------------------------------------------------------

    jwt_secret: str = Field(
        ...,
        min_length=32,
        description="Strong secret used for signing JWT tokens",
    )

    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24

    # ---------------------------------------------------------
    # AI
    # ---------------------------------------------------------

    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"

    # ---------------------------------------------------------
    # WEB SEARCH
    # ---------------------------------------------------------

    tavily_api_key: str = ""

    # ---------------------------------------------------------
    # EMBEDDINGS
    # ---------------------------------------------------------

    embedding_model: str = "all-MiniLM-L6-v2"
    rag_semantic_weight: float = 0.6
    rag_lexical_weight: float = 0.4
    rag_candidate_pool_size: int = 30
    rag_final_k: int = 6
    rag_context_max_chars: int = 12000

    # ---------------------------------------------------------
    # FRONTEND / CORS
    # ---------------------------------------------------------

    frontend_url: str = "http://localhost:3000"

    # ---------------------------------------------------------
    # FILE UPLOAD
    # ---------------------------------------------------------

    max_upload_mb: int = 15

    # ---------------------------------------------------------
    # RATE LIMITING
    # ---------------------------------------------------------

    rate_limit_login_per_minute: int = 5
    rate_limit_register_per_minute: int = 5
    rate_limit_chat_per_minute: int = 20
    rate_limit_upload_per_minute: int = 10

    # ---------------------------------------------------------
    # VALIDATION
    # ---------------------------------------------------------

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, value: str) -> str:
        allowed = {"development", "staging", "production"}

        value = value.lower().strip()

        if value not in allowed:
            raise ValueError(
                f"ENVIRONMENT must be one of: {', '.join(sorted(allowed))}"
            )

        return value

    @field_validator("jwt_secret")
    @classmethod
    def validate_jwt_secret(cls, value: str) -> str:
        value = value.strip()

        if len(value) < 32:
            raise ValueError(
                "JWT_SECRET must contain at least 32 characters."
            )

        return value

    @field_validator("frontend_url")
    @classmethod
    def validate_frontend_url(cls, value: str) -> str:
        return value.rstrip("/")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()