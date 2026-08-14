from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 数据库
    DATABASE_URL: str = "postgresql+asyncpg://harness:harness_dev_pw@localhost:5432/harness"

    # JWT 双 Token
    JWT_SECRET: str = "change-me-in-prod-please"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # CORS
    CORS_ORIGINS: str = "http://localhost:8080"

    # AI 模块（AI_API_KEY 为空时进入 mock 模式）
    AI_API_KEY: str = ""
    AI_BASE_URL: str = "https://api.deepseek.com/v1"
    AI_MODEL: str = "deepseek-chat"

    # 文件上传
    UPLOAD_DIR: str = "/app/uploads"
    MAX_AVATAR_SIZE: int = 2 * 1024 * 1024  # 2MB

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
