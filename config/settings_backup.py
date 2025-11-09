"""
Configuration management for FMNA platform
Uses pydantic-settings for environment variable management
"""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field, validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # API Keys
    fmp_api_key: str = Field(default="", description="Financial Modeling Prep API key")
    deepseek_api_key: str = Field(default="", description="DeepSeek API key")
    sec_api_key: Optional[str] = Field(None, description="SEC API key (optional)")
    
    # Database Configuration
    postgres_host: str = Field(default="localhost", description="PostgreSQL host")
    postgres_port: int = Field(default=5432, description="PostgreSQL port")
    postgres_db: str = Field(default="fmna", description="PostgreSQL database name")
    postgres_user: str = Field(default="fmna_user", description="PostgreSQL username")
    postgres_password: str = Field(default="demo_password", description="PostgreSQL password")
    
    # Redis Configuration
    redis_host: str = Field(default="localhost", description="Redis host")
    redis_port: int = Field(default=6379, description="Redis port")
    redis_db: int = Field(default=0, description="Redis database number")
    redis_password: Optional[str] = Field(None, description="Redis password")
    
    # MongoDB Configuration
    mongo_uri: str = Field(default="mongodb://localhost:27017/fmna", description="MongoDB URI")
    
    # Cognee Configuration (open-source, no API key needed)
    cognee_enabled: bool = Field(default=True, description="Enable Cognee knowledge graph")
    
    # Application Settings
    environment: str = Field(default="development", description="Environment: development, staging, production")
    log_level: str = Field(default="INFO", description="Logging level")
    debug: bool = Field(default=True, description="Debug mode")
    
    # Data Storage Paths
    data_dir: Path = Field(default=Path("data"), description="Data directory")
    raw_data_dir: Path = Field(default=Path("data/raw"), description="Raw data directory")
    processed_data_dir: Path = Field(default=Path("data/processed"), description="Processed data directory")
    models_dir: Path = Field(default=Path("data/models"), description="Models directory")
    outputs_dir: Path = Field(default=Path("outputs"), description="Outputs directory")
    
    # LLM Configuration
    llm_provider: str = Field(default="deepseek", description="LLM provider")
    llm_model: str = Field(default="deepseek-reasoner", description="LLM model name")
    llm_endpoint: Optional[str] = Field(None, description="LLM API endpoint URL (for custom providers)")
    llm_api_key: Optional[str] = Field(None, description="LLM API key (for custom providers)")
    llm_temperature: float = Field(default=0.1, description="LLM temperature")
    llm_max_tokens: int = Field(default=32000, description="LLM max tokens")
    
    # Financial Data Settings
    default_period: str = Field(default="ttm", description="Default period for financial data: 'annual', 'quarter', or 'ttm' (trailing twelve months)")
    
    # Rate Limiting
    fmp_rate_limit: int = Field(default=300, description="FMP API rate limit (requests per minute)")
    sec_rate_limit: int = Field(default=10, description="SEC rate limit (requests per second)")
    
    # Prefect/Orchestration
    prefect_api_url: str = Field(default="http://localhost:4200/api", description="Prefect API URL")
    
    # Security
    secret_key: str = Field(default="demo_secret_key_change_in_production", description="Secret key for encryption")
    jwt_secret: str = Field(default="demo_jwt_secret_change_in_production", description="JWT secret for authentication")
    
    # Frontend
    frontend_url: str = Field(default="http://localhost:3000", description="Frontend URL")
    backend_url: str = Field(default="http://localhost:8000", description="Backend URL")
    
    @validator("data_dir", "raw_data_dir", "processed_data_dir", "models_dir", "outputs_dir")
    def ensure_path_exists(cls, v: Path) -> Path:
        """Ensure directory exists"""
        v.mkdir(parents=True, exist_ok=True)
        return v
    
    @property
    def postgres_url(self) -> str:
        """Construct PostgreSQL connection URL"""
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
    
    @property
    def redis_url(self) -> str:
        """Construct Redis connection URL"""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"
    
    @property
    def deepseek_api_url(self) -> str:
        """DeepSeek API base URL"""
        return "https://api.deepseek.com/v1"
    
    @property
    def fmp_base_url(self) -> str:
        """FMP API base URL"""
        return "https://financialmodelingprep.com/api/v3"
    
    @property
    def sec_edgar_url(self) -> str:
        """SEC EDGAR base URL"""
        return "https://www.sec.gov/cgi-bin/browse-edgar"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "allow"  # Allow extra environment variables for Cognee


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create settings instance"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """Reload settings from environment"""
    global _settings
    _settings = Settings()
    return _settings
