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

    # MQTT（IoT 遥测；容器内用服务名 mqtt，本地开发用 127.0.0.1）
    MQTT_HOST: str = "mqtt"
    MQTT_PORT: int = 1883
    MQTT_TOPIC_PREFIX: str = "harness"

    # 邮箱验证码 / SMTP
    SMTP_HOST: str = ""
    SMTP_PORT: int = 465
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = ""
    EMAIL_CODE_EXPIRE_MINUTES: int = 5
    EMAIL_CODE_RESEND_SECONDS: int = 60
    EMAIL_CODE_MAX_ATTEMPTS: int = 5

    # GitHub OAuth（SSO 登录；两个值都为空时第三方登录入口自动隐藏）
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""
    # 站点对外地址（构建 OAuth 回调地址与前端落地页跳转；开发用 http://localhost:5173）
    PUBLIC_BASE_URL: str = "http://localhost:5173"

    @property
    def smtp_enabled(self) -> bool:
        return bool(self.SMTP_HOST and self.SMTP_USER and self.SMTP_PASSWORD)

    @property
    def github_oauth_enabled(self) -> bool:
        return bool(self.GITHUB_CLIENT_ID and self.GITHUB_CLIENT_SECRET)

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
