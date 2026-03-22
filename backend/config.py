from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    environment: str = "development"

    lm_studio_url: str = "http://localhost:1234/v1"
    lm_studio_model: str = "local-model"
    lm_studio_timeout: int = 2400  # 40-minute timeout for very long LMStudio generations

    backend_host: str = "127.0.0.1"
    backend_port: int = 8000
    projects_dir: str = "projects"
    db_path: str = "novelforge.db"

    context_token_budget: int = 6000
    max_generation_tokens: int = 4000
    words_per_chapter_default: int = 3000

    frontend_origin: str = "http://localhost:5173"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def is_dev(self) -> bool:
        return self.environment == "development"

    @property
    def projects_path(self) -> Path:
        p = Path(self.projects_dir)
        p.mkdir(exist_ok=True)
        return p


settings = Settings()
