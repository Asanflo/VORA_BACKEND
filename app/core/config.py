from typing import List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
import json
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "VORA Mobility Backend"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Database: SupaBase (PostgreSQL) or SQLite
    DATABASE_URL: str 
    
    # SupaBase Credentials
    SUPABASE_URL: str 
    SUPABASE_KEY: str 
    SUPABASE_STORAGE_BUCKET: str 

    # Security & Auth
    SECRET_KEY: str 
    ALGORITHM: str  
    ACCESS_TOKEN_EXPIRE_MINUTES: int  

    # Payment Aggregator (Escrow MoMo / OM)
    PAYMENT_AGGREGATOR_MODE: str 
    PAYMENT_AGGREGATOR_API_KEY: str 
    PAYMENT_AGGREGATOR_API_SECRET: str 
    VORA_COMMISSION_PERCENTAGE: float 

    # AI Voice (Gemini)
    GEMINI_API_KEY: str 
    GEMINI_MODEL: str 

    # CORS
    ALLOWED_ORIGINS: Union[List[str], str] 

    # Local uploads fallback directory
    UPLOAD_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "uploads")

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, str) and v.startswith("["):
            return json.loads(v)
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

