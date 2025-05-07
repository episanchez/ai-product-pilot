from pydantic_settings import BaseSettings
from typing import Optional
import os
from dotenv import load_dotenv

# Charger les variables d'environnement depuis .env
load_dotenv()


class Settings(BaseSettings):
    # Application
    debug: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    
    # Supabase
    supabase_url: str = os.getenv("SUPABASE_URL", "")
    supabase_service_key: str = os.getenv("SUPABASE_SERVICE_KEY", "")
    supabase_anon_key: str = os.getenv("SUPABASE_ANON_KEY", "")
    
    # OpenAI
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    
    # LangSmith
    langchain_api_key: Optional[str] = os.getenv("LANGCHAIN_API_KEY")
    langchain_project: Optional[str] = os.getenv("LANGCHAIN_PROJECT", "feedback-analytics")
    langchain_tracing_v2: bool = os.getenv("LANGCHAIN_TRACING_V2", "").lower() in ("true", "1", "t")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Instance globale des paramètres
settings = Settings()