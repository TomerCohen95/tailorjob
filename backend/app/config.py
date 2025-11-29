from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional
import json

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"  # Ignore extra fields in .env
    )
    
    API_TITLE: str = "TailorJob API"
    API_VERSION: str = "1.0.0"
    
    SUPABASE_URL: str
    SUPABASE_KEY: str
    
    UPSTASH_REDIS_URL: Optional[str] = ""
    
    AZURE_OPENAI_ENDPOINT: Optional[str] = ""
    AZURE_OPENAI_KEY: Optional[str] = ""
    AZURE_OPENAI_DEPLOYMENT: str = "gpt-4"
    AZURE_OPENAI_DEPLOYMENT_MINI: str = "gpt-4o-mini"  # For v5.0 extraction
    AZURE_OPENAI_DEPLOYMENT_GPT4: str = "gpt-4"        # For v5.0 analysis
    AZURE_OPENAI_API_VERSION: str = "2024-08-01-preview"
    
    CORS_ORIGINS: str = '["http://localhost:5173","http://localhost:8080"]'
    
    # Matcher Version Control
    USE_MATCHER_V5: bool = False  # Enable v5.0 Fully AI-driven (GPT-4)
    USE_MATCHER_V4: bool = True   # Enable v4.0 Extract→Normalize→Compare→Score→Explain
    USE_MATCHER_V3: bool = False  # Enable v3.0 AI-first matcher
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS_ORIGINS from JSON string to list"""
        try:
            return json.loads(self.CORS_ORIGINS)
        except:
            return ["http://localhost:5173"]

settings = Settings()