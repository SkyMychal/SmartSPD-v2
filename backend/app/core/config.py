"""
Application configuration settings
"""
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings
from typing import List, Optional
import os
from pathlib import Path

class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    APP_NAME: str = Field(default="SmartSPD", env="APP_NAME")
    APP_VERSION: str = Field(default="2.0.0", env="APP_VERSION")
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=True, env="DEBUG")
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Database
    DATABASE_URL: str = Field(env="DATABASE_URL")
    
    # Redis
    REDIS_URL: str = Field(env="REDIS_URL")
    
    # Neo4j
    NEO4J_URI: str = Field(env="NEO4J_URI")
    NEO4J_USER: str = Field(env="NEO4J_USER")
    NEO4J_PASSWORD: str = Field(env="NEO4J_PASSWORD")
    
    # API Keys
    OPENAI_API_KEY: str = Field(env="OPENAI_API_KEY")
    PINECONE_API_KEY: str = Field(env="PINECONE_API_KEY")
    
    # Azure OpenAI Configuration
    AZURE_OPENAI_ENDPOINT: Optional[str] = Field(default=None, env="AZURE_OPENAI_ENDPOINT")
    AZURE_OPENAI_API_KEY: Optional[str] = Field(default=None, env="AZURE_OPENAI_API_KEY")
    AZURE_OPENAI_API_VERSION: str = Field(default="2024-02-15-preview", env="AZURE_OPENAI_API_VERSION")
    AZURE_OPENAI_GPT4_DEPLOYMENT: str = Field(default="gpt-4", env="AZURE_OPENAI_GPT4_DEPLOYMENT")
    AZURE_OPENAI_GPT35_DEPLOYMENT: str = Field(default="gpt-35-turbo", env="AZURE_OPENAI_GPT35_DEPLOYMENT")
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT: str = Field(default="text-embedding-ada-002", env="AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
    
    # AI Service Provider Selection
    AI_SERVICE_PROVIDER: str = Field(default="openai", env="AI_SERVICE_PROVIDER")
    
    # Pinecone Configuration
    PINECONE_ENVIRONMENT: str = Field(default="gcp-starter", env="PINECONE_ENVIRONMENT")
    PINECONE_INDEX_NAME: str = Field(default="smartspd-vectors", env="PINECONE_INDEX_NAME")
    
    # Security
    JWT_SECRET_KEY: str = Field(env="JWT_SECRET_KEY")
    JWT_ALGORITHM: str = Field(default="HS256", env="JWT_ALGORITHM")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=480, env="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")  # 8 hours
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=30, env="JWT_REFRESH_TOKEN_EXPIRE_DAYS")  # 30 days
    
    # CORS
    CORS_ORIGINS: str = Field(default="http://localhost:3000", env="CORS_ORIGINS")
    
    # File Upload
    MAX_FILE_SIZE_MB: int = Field(default=100, env="MAX_FILE_SIZE_MB")
    UPLOAD_DIRECTORY: str = Field(default="./uploads", env="UPLOAD_DIRECTORY")
    ALLOWED_FILE_TYPES: str = Field(default="pdf,xlsx,xls,csv", env="ALLOWED_FILE_TYPES")
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")
    RATE_LIMIT_PER_HOUR: int = Field(default=1000, env="RATE_LIMIT_PER_HOUR")

    # Cloud Storage
    CLOUD_STORAGE_BUCKET_PATH: str = Field(default="./cloud_storage", env="CLOUD_STORAGE_BUCKET_PATH")
    
    # Auth0 Configuration
    AUTH0_DOMAIN: Optional[str] = Field(default=None, env="AUTH0_DOMAIN")
    AUTH0_CLIENT_ID: Optional[str] = Field(default=None, env="AUTH0_CLIENT_ID")
    AUTH0_CLIENT_SECRET: Optional[str] = Field(default=None, env="AUTH0_CLIENT_SECRET")
    AUTH0_AUDIENCE: Optional[str] = Field(default=None, env="AUTH0_AUDIENCE")
    
    # Email (Optional)
    SMTP_HOST: Optional[str] = Field(default=None, env="SMTP_HOST")
    SMTP_PORT: int = Field(default=587, env="SMTP_PORT")
    SMTP_USER: Optional[str] = Field(default=None, env="SMTP_USER")
    SMTP_PASSWORD: Optional[str] = Field(default=None, env="SMTP_PASSWORD")
    FROM_EMAIL: str = Field(default="noreply@smartspd.com", env="FROM_EMAIL")
    
    
    @property
    def MAX_FILE_SIZE_BYTES(self) -> int:
        return self.MAX_FILE_SIZE_MB * 1024 * 1024
    
    @property
    def UPLOAD_PATH(self) -> Path:
        path = Path(self.UPLOAD_DIRECTORY)
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @property
    def CORS_ORIGINS_LIST(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    @property
    def ALLOWED_FILE_TYPES_LIST(self) -> List[str]:
        return [file_type.strip() for file_type in self.ALLOWED_FILE_TYPES.split(",")]
    
    model_config = {
        "env_file": [".env.development", ".env"],
        "case_sensitive": True,
        "extra": "allow"
    }

# Create settings instance
settings = Settings()