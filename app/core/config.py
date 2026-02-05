"""Application configuration"""
from pydantic import model_validator
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    app_name: str = "TrueVow Financial Management Service"
    app_version: str = "1.0.0"
    environment: str = "development"
    debug: bool = False
    
    # Database
    # Support both DATABASE_URL and FINANCIAL_MANAGEMENT_DATABASE_URL
    database_url: Optional[str] = None
    financial_management_database_url: Optional[str] = None
    financial_management_database_transaction_pooler_url: Optional[str] = None
    financial_management_database_session_pooler_url: Optional[str] = None
    database_pool_size: int = 10
    database_max_overflow: int = 20
    
    @property
    def effective_database_url(self) -> str:
        """Get the effective database URL, preferring transaction pooler > session pooler > DATABASE_URL > direct DB"""
        # Prefer transaction pooler for long-running operations (migrations, seeding) - more stable than session pooler
        if self.financial_management_database_transaction_pooler_url:
            url = self.financial_management_database_transaction_pooler_url
            if url.startswith("postgresql://") and "+asyncpg" not in url:
                url = url.replace("postgresql://", "postgresql+asyncpg://")
            return url
        # Session pooler for runtime API requests
        elif self.financial_management_database_session_pooler_url:
            url = self.financial_management_database_session_pooler_url
            if url.startswith("postgresql://") and "+asyncpg" not in url:
                url = url.replace("postgresql://", "postgresql+asyncpg://")
            return url
        elif self.database_url:
            return self.database_url
        elif self.financial_management_database_url:
            # Direct DB URL (port 5432)
            url = self.financial_management_database_url
            if url.startswith("postgresql://") and "+asyncpg" not in url:
                url = url.replace("postgresql://", "postgresql+asyncpg://")
            return url
        else:
            raise ValueError("Either DATABASE_URL or FINANCIAL_MANAGEMENT_DATABASE_URL must be set")
    
    # Security: JWT secret from JWT_SECRET_KEY or FINANCIAL_MANAGEMENT_SECRET_KEY (.env.local)
    jwt_secret_key: Optional[str] = None
    financial_management_secret_key: Optional[str] = None  # env: FINANCIAL_MANAGEMENT_SECRET_KEY

    @model_validator(mode="after")
    def require_jwt_secret(self) -> "Settings":
        self.jwt_secret_key = self.jwt_secret_key or self.financial_management_secret_key
        if not self.jwt_secret_key and self.environment == "development":
            self.jwt_secret_key = "dev-secret-change-in-production"
        if not self.jwt_secret_key:
            raise ValueError("JWT_SECRET_KEY or FINANCIAL_MANAGEMENT_SECRET_KEY must be set")
        return self

    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 30
    
    # Auth Service Integration
    auth_service_url: Optional[str] = None
    
    # Billing Service Integration
    billing_service_url: Optional[str] = None
    billing_service_token: Optional[str] = None
    billing_api_url: Optional[str] = None  # Alias for backward compatibility
    billing_api_key: Optional[str] = None  # Alias for backward compatibility
    
    # Treasury Service Integration
    treasury_api_url: Optional[str] = None
    treasury_api_key: Optional[str] = None
    
    # Observability
    log_level: str = "INFO"
    enable_metrics: bool = True
    
    class Config:
        env_file = [".env", ".env.local"]  # Check both .env and .env.local
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from .env.local


settings = Settings()
