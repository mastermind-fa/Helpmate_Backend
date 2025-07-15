from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./helpmate.db"
    
    # JWT
    secret_key: str = "your-secret-key-here-make-it-long-and-secure"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Email (for future use)
    smtp_server: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    
    # App
    app_name: str = "HelpMate API"
    debug: bool = True
    base_url: str = "http://localhost:8000"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings() 