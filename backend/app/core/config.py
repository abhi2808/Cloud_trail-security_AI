"""
Application configuration using Pydantic BaseSettings.
All environment variables are declared here with typed fields.
"""

from typing import Literal
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # AWS Configuration
    aws_region: str = Field(default="us-east-1", description="AWS region for CloudTrail queries")

    # AI Provider Configuration
    gemini_api_key: str = Field(default="", description="Google Gemini API key")
    groq_api_key: str = Field(default="", description="Groq API key")
    ai_provider: Literal["gemini", "groq"] = Field(
        default="gemini", description="Active AI provider: gemini or groq"
    )

    # Application Configuration
    port: int = Field(default=8000, description="Backend server port")
    client_url: str = Field(
        default="http://localhost:5173", description="Frontend client URL for CORS"
    )

    # MongoDB Configuration
    mongodb_uri: str = Field(..., description="MongoDB URI")

    # JWT Authentication
    jwt_secret: str = Field(..., description="JWT Secret For Hashing")
    jwt_expiry_hours: int = Field(default=24, description="JWT Expiry in Hours")

    # AWS Key Encryption
    encryption_secret: str = Field(..., description="Fernet Key Encryption Secret")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
    }


settings = Settings()
