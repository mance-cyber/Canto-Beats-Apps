"""
Configuration management for License Distribution Server
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""
    
    # App
    app_name: str = "Canto-beats License Server"
    debug: bool = False
    
    # Database
    database_url: str = "sqlite:///./licenses.db"
    
    # Stripe
    stripe_api_key: str
    stripe_webhook_secret: str
    stripe_price_id: Optional[str] = None  # Product price ID
    
    # SendGrid
    sendgrid_api_key: str
    sendgrid_from_email: str = "noreply@cantobeats.com"
    sendgrid_from_name: str = "Canto-beats"
    
    # Admin
    admin_username: str = "admin"
    admin_password: str  # Should be hashed in production
    
    # License Settings
    license_transfers_allowed: int = 1
    license_type: str = "permanent"  # or "trial"
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
