from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    supabase_url: str
    supabase_service_key: str
    github_token: str
    github_username: str
    anthropic_api_key: str
    backend_api_key: str
    cors_origin: str

    class Config:
        env_file = ".env"


settings = Settings()
