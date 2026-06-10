"""
应用配置管理
使用 Pydantic Settings 从环境变量/.env 文件加载配置
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """应用全局配置"""

    # ========== 应用基础 ==========
    APP_NAME: str = "Research Paper Assistant"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    SECRET_KEY: str = "change-me-in-production-use-a-random-string"

    # ========== 数据库 ==========
    POSTGRES_HOST: str = "db"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "paper_assistant"

    @property
    def DATABASE_URL(self) -> str:
        """异步数据库连接 URL"""
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def DATABASE_URL_SYNC(self) -> str:
        """同步数据库连接 URL (alembic 迁移用)"""
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # ========== Redis ==========
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # ========== JWT 认证 ==========
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30     # 访问令牌 30 分钟过期
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7        # 刷新令牌 7 天过期

    # ========== DeepSeek API ==========
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/v1"
    DEEPSEEK_MODEL: str = "deepseek-chat"      # deepseek-chat 或 deepseek-reasoner

    # ========== Embedding 模型 ==========
    EMBEDDING_MODEL: str = "BAAI/bge-m3"
    EMBEDDING_DEVICE: str = "cpu"              # Docker 中无 GPU，本地开发可改为 cuda

    # ========== 文件上传 ==========
    UPLOAD_DIR: str = "/app/uploads"           # PDF 上传存储目录
    MAX_UPLOAD_SIZE_MB: int = 50               # 最大上传文件大小 (MB)

    # ========== 外部 API ==========
    ARXIV_API_BASE: str = "https://export.arxiv.org/api/query"
    SEMANTIC_SCHOLAR_API_BASE: str = "https://api.semanticscholar.org/graph/v1"

    # ========== CORS ==========
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",               # Vite 开发服务器
        "http://localhost:3000",
        "http://localhost",
    ]

    model_config = {"env_file": ".env", "case_sensitive": True}


# 全局配置单例
settings = Settings()
