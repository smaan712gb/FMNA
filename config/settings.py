"""
Configuration management for FMNA platform
Supports both Streamlit Cloud secrets and local .env files
"""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field, validator

# Try to import streamlit to check if we're in Streamlit environment
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False


def get_secret(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Get secret from Streamlit secrets (cloud) or environment variable (local)
    
    Priority:
    1. Streamlit secrets (st.secrets) - for Streamlit Cloud deployment
    2. Environment variables (os.getenv) - for local development with .env file
    3. Default value if provided
    
    Args:
        key: Secret key name
        default: Default value if not found
        
    Returns:
        Secret value or default
    """
    # Priority 1: Check Streamlit secrets (for cloud deployment)
    if STREAMLIT_AVAILABLE:
        try:
            if key in st.secrets:
                value = st.secrets[key]
                if value and str(value).strip():
                    return str(value).strip()
        except Exception:
            # st.secrets might not be available in all contexts
            pass
    
    # Priority 2: Check environment variables (for local .env)
    env_value = os.getenv(key)
    if env_value and env_value.strip():
        return env_value.strip()
    
    # Priority 3: Return default
    return default


class Settings(BaseSettings):
    """Application settings with Streamlit Cloud support and all required attributes"""
    
    # API Keys - will check st.secrets first, then .env
    fmp_api_key: str = Field(
        default_factory=lambda: get_secret('FMP_API_KEY', ''),
        description="Financial Modeling Prep API key"
    )
    
    deepseek_api_key: str = Field(
        default_factory=lambda: get_secret('DEEPSEEK_API_KEY', ''),
        description="DeepSeek API key"
    )
    
    sec_api_key: Optional[str] = Field(None, description="SEC API key (optional)")
    
    # Database Configuration
    postgres_host: str = Field(default="localhost", description="PostgreSQL host")
    postgres_port: int = Field(default=5432, description="PostgreSQL port")
    postgres_db: str = Field(default="fmna", description="PostgreSQL database name")
    postgres_user: str = Field(default="fmna_user", description="PostgreSQL username")
    postgres_password: str = Field(default="demo_password", description="PostgreSQL password")
    
    # Redis Configuration
    redis_host: str = Field(
        default_factory=lambda: get_secret('REDIS_HOST', 'localhost'),
        description="Redis host"
    )
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
    llm_model: str = Field(
        default_factory=lambda: get_secret('LLM_MODEL', 'deepseek-reasoner'),
        description="LLM model name"
    )
    llm_endpoint: Optional[str] = Field(None, description="LLM API endpoint URL (for custom providers)")
    llm_api_key: Optional[str] = Field(None, description="LLM API key (for custom providers)")
    llm_temperature: float = Field(default=0.1, description="LLM temperature")
    llm_max_tokens: int = Field(
        default_factory=lambda: int(get_secret('LLM_MAX_TOKENS', '32000')),
        description="LLM max tokens"
    )
    
    # Financial Data Settings
    default_period: str = Field(
        default_factory=lambda: get_secret('DEFAULT_PERIOD', 'ttm'),
        description="Default period for financial data: 'annual', 'quarter', or 'ttm' (trailing twelve months)"
    )
    
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
    
    # Database Configuration (for compatibility)
    duckdb_path: str = Field(default="data/fmna.duckdb", description="DuckDB database path")
    
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
    
    def validate_api_keys(self) -> dict:
        """
        Validate that required API keys are configured
        
        Returns:
            Dictionary with validation results
        """
        results = {
            'fmp_configured': bool(self.fmp_api_key and self.fmp_api_key.strip()),
            'deepseek_configured': bool(self.deepseek_api_key and self.deepseek_api_key.strip()),
            'environment': 'streamlit_cloud' if STREAMLIT_AVAILABLE and hasattr(st, 'secrets') else 'local',
            'errors': []
        }
        
        if not results['fmp_configured']:
            results['errors'].append(
                "FMP_API_KEY not configured. "
                "Add it to Streamlit secrets (cloud) or .env file (local)"
            )
        
        if not results['deepseek_configured']:
            results['errors'].append(
                "DEEPSEEK_API_KEY not configured (AI features will be limited). "
                "Add it to Streamlit secrets (cloud) or .env file (local)"
            )
        
        return results
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get global settings instance (singleton pattern)
    
    Returns:
        Settings instance
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """
    Force reload settings (useful after updating secrets)
    
    Returns:
        New Settings instance
    """
    global _settings
    _settings = Settings()
    return _settings


# Helper function for easy access
def get_api_key(service: str) -> Optional[str]:
    """
    Get API key for a specific service
    
    Args:
        service: Service name ('fmp' or 'deepseek')
        
    Returns:
        API key or None
    """
    settings = get_settings()
    
    if service.lower() == 'fmp':
        return settings.fmp_api_key
    elif service.lower() == 'deepseek':
        return settings.deepseek_api_key
    else:
        return None
