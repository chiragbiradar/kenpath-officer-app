from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///:memory:"
    jwt_secret: str = "test-secret-change-in-production"
    jwt_expire_minutes: int = 480
    gemini_api_key: str = ""
    llm_model: str = "gemini-1.5-flash"
    prompt_version: str = "v1"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
