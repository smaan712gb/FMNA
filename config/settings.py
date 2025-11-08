"""
Settings Configuration
Supports both Streamlit Cloud secrets and local .env files
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field

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
        except Exception as e:
            # st.secrets might not be available in all contexts
            pass
    
    # Priority 2: Check environment variables (for local .env)
    env_value = os.getenv(key)
    if env_value and env_value.strip():
        return env_value.strip()
    
    # Priority 3: Return default
    return default


class Settings(BaseSettings):
    """Application settings with Streamlit Cloud support"""
    
    # API Keys - will check st.secrets first, then .env
    fmp_api_key: str = Field(
        default_factory=lambda: get_secret('FMP_API_KEY', ''),
        description="Financial Modeling Prep API Key"
    )
    
    deepseek_api_key: str = Field(
        default_factory=lambda: get_secret('DEEPSEEK_API_KEY', ''),
        description="DeepSeek API Key for LLM"
    )
    
    # LLM Configuration
    llm_model: str = Field(
        default_factory=lambda: get_secret('LLM_MODEL', 'deepseek-reasoner'),
        description="LLM model to use"
    )
    
    llm_max_tokens: int = Field(
        default_factory=lambda: int(get_secret('LLM_MAX_TOKENS', '32000')),
        description="Maximum tokens for LLM responses"
    )
    
    llm_temperature: float = Field(
        default=0.1,
        description="LLM temperature for reasoning"
    )
    
    # FMP Configuration
    fmp_base_url: str = Field(
        default="https://financialmodelingprep.com/api/v3",
        description="FMP API base URL"
    )
    
    fmp_rate_limit: int = Field(
        default=300,
        description="FMP API rate limit (calls per minute)"
    )
    
    # SEC Configuration
    sec_rate_limit: int = Field(
        default=10,
        description="SEC rate limit (requests per second)"
    )
    
    # Data Configuration
    default_period: str = Field(
        default_factory=lambda: get_secret('DEFAULT_PERIOD', 'annual'),
        description="Default period for financial data (annual/quarter/ttm)"
    )
    
    # Database Configuration
    duckdb_path: str = Field(
        default="data/fmna.duckdb",
        description="DuckDB database path"
    )
    
    # Redis Configuration (optional)
    redis_host: str = Field(
        default_factory=lambda: get_secret('REDIS_HOST', 'localhost'),
        description="Redis host"
    )
    
    redis_port: int = Field(
        default=6379,
        description="Redis port"
    )
    
    # Application Configuration
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )
    
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
