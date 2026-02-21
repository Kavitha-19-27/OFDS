"""
Configuration management using Pydantic Settings.
Loads environment variables with validation and type coercion.
"""
import os
from functools import lru_cache
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """Application settings with environment variable loading."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Application
    app_name: str = Field(default="RAG-SaaS")
    app_env: str = Field(default="development")
    debug: bool = Field(default=False)
    api_v1_prefix: str = Field(default="/api/v1")
    
    # Server
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    
    # Database - Support Render's postgres:// format
    database_url: str = Field(default="sqlite+aiosqlite:///./data/app.db")
    
    @field_validator("database_url", mode="before")
    @classmethod
    def fix_database_url(cls, v: str) -> str:
        """Convert postgres:// to postgresql:// for SQLAlchemy."""
        if v and v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql://", 1)
        return v
    
    # JWT - Support both SECRET_KEY and JWT_SECRET_KEY
    jwt_secret_key: str = Field(default="")
    secret_key: str = Field(default="")  # Fallback for Render
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    
    @property
    def effective_jwt_secret(self) -> str:
        """Get the effective JWT secret key."""
        key = self.jwt_secret_key or self.secret_key or os.getenv("SECRET_KEY", "")
        if not key or key == "change-this-super-secret-key-in-production-minimum-32-characters-long":
            if self.is_production:
                raise ValueError("JWT_SECRET_KEY must be set in production!")
            return "dev-secret-key-not-for-production-use-32chars"
        return key
    
    # LLM Provider
    llm_provider: str = Field(default="groq")  # openai or groq
    
    # OpenAI (optional)
    openai_api_key: str = Field(default="")
    openai_embedding_model: str = Field(default="text-embedding-3-small")
    openai_chat_model: str = Field(default="gpt-4o-mini")
    openai_embedding_dimensions: int = Field(default=1536)
    
    # Groq
    groq_api_key: str = Field(default="")
    groq_chat_model: str = Field(default="llama-3.3-70b-versatile")
    
    # Local Embeddings - Default to True for Render (no OpenAI needed)
    use_local_embeddings: bool = Field(default=True)
    local_embedding_model: str = Field(default="all-MiniLM-L6-v2")
    local_embedding_dimensions: int = Field(default=384)
    
    # FAISS
    faiss_index_path: str = Field(default="./data/faiss_indexes")
    faiss_cache_size: int = Field(default=5)  # Reduced for Render memory
    
    # RAG
    chunk_size: int = Field(default=450)
    chunk_overlap: int = Field(default=80)
    top_k_retrieval: int = Field(default=4)
    
    # File Upload
    max_file_size_mb: int = Field(default=10)
    upload_path: str = Field(default="./data/uploads")
    allowed_extensions: str = Field(default=".pdf")
    
    # Rate Limiting
    rate_limit_per_minute: int = Field(default=60)
    rate_limit_per_hour: int = Field(default=1000)
    
    # CORS - Set your actual frontend URL(s) here
    # Note: Wildcards don't work with credentials, use specific URLs
    cors_origins: str = Field(default="http://localhost:5173,http://localhost:3000")
    cors_allow_credentials: bool = Field(default=True)
    
    # Logging
    log_level: str = Field(default="INFO")
    log_format: str = Field(default="json")
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins string into list, handling wildcards."""
        origins = [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
        # If "*" is present, allow all origins (but won't work with credentials)
        if "*" in origins:
            return ["*"]
        return origins
    
    @property
    def allowed_extensions_list(self) -> List[str]:
        """Parse allowed extensions into list."""
        return [ext.strip() for ext in self.allowed_extensions.split(",")]
    
    @property
    def max_file_size_bytes(self) -> int:
        """Convert MB to bytes."""
        return self.max_file_size_mb * 1024 * 1024
    
    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.app_env.lower() == "production"


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Using lru_cache ensures settings are only loaded once per process.
    """
    return Settings()


# Export settings instance for easy import
settings = get_settings()
