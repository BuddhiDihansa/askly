from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    mongodb_uri: str

    # SECURITY FIX: no insecure default. If JWT_SECRET is missing from .env,
    # the app now fails to start with a clear error instead of silently
    # running with a publicly-known secret ("change-me") that would let
    # anyone forge a valid login token.
    jwt_secret: str

    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    tavily_api_key: str = ""
    frontend_url: str = "http://localhost:3000"
    embedding_model: str = "all-MiniLM-L6-v2"
    max_upload_mb: int = 15

    # rate limiting (see app/core/rate_limit.py)
    rate_limit_login_per_minute: int = 5
    rate_limit_chat_per_minute: int = 20

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")


settings = Settings()
