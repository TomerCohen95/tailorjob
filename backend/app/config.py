from pydantic_settings import BaseSettings
from typing import List
import json

class Settings(BaseSettings):
    API_TITLE: str = "TailorJob API"
    API_VERSION: str = "1.0.0"
    
    SUPABASE_URL: str
    SUPABASE_KEY: str
    
    UPSTASH_REDIS_URL: str
    
    AZURE_OPENAI_ENDPOINT: str
    AZURE_OPENAI_KEY: str
    AZURE_OPENAI_DEPLOYMENT: str = "gpt-4"
    
    CORS_ORIGINS: str = '["http://localhost:5173"]'
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS_ORIGINS from JSON string to list"""
        try:
            return json.loads(self.CORS_ORIGINS)
        except:
            return ["http://localhost:5173"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()