"""
Smart English Test-Prep Agent - Configuration Management
Centralized configuration with environment variable handling
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings


# Load environment variables
load_dotenv()


# Project paths
BASE_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = BASE_DIR / 'backend'
DATA_DIR = BASE_DIR / 'data'
OUTPUT_DIR = BASE_DIR / 'output'
LOGS_DIR = BASE_DIR / 'logs'

# Create directories if they don't exist
for directory in [DATA_DIR, OUTPUT_DIR, LOGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)


class DatabaseConfig(BaseSettings):
    """Database configuration settings."""

    host: str = Field(default="localhost", alias="DB_HOST")
    port: int = Field(default=5432, alias="DB_PORT")
    name: str = Field(default="english_testprep", alias="DB_NAME")
    user: str = Field(default="user", alias="DB_USER")
    password: str = Field(default="password", alias="DB_PASSWORD")

    @property
    def url(self) -> str:
        """Generate database connection URL."""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"

    class Config:
        env_file = ".env"
        extra = "ignore"


class LLMConfig(BaseSettings):
    """LLM API configuration."""

    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    model: str = Field(default="claude-sonnet-4-20250514")
    temperature: float = Field(default=0.7)
    max_tokens: int = Field(default=4000)

    class Config:
        env_file = ".env"
        extra = "ignore"


class TestConfig(BaseSettings):
    """Test configuration settings."""

    daily_test_duration_minutes: int = Field(default=15, alias="DAILY_TEST_DURATION_MINUTES")
    daily_test_question_count: int = Field(default=15, alias="DAILY_TEST_QUESTION_COUNT")
    mega_test_duration_minutes: int = Field(default=60, alias="MEGA_TEST_DURATION_MINUTES")
    mega_test_question_count: int = Field(default=50, alias="MEGA_TEST_QUESTION_COUNT")
    mega_test_interval_days: int = Field(default=14, alias="MEGA_TEST_INTERVAL_DAYS")

    class Config:
        env_file = ".env"
        extra = "ignore"


class APIConfig(BaseSettings):
    """API configuration settings."""

    host: str = Field(default="0.0.0.0", alias="API_HOST")
    port: int = Field(default=8000, alias="API_PORT")
    debug: bool = Field(default=False, alias="API_DEBUG")
    frontend_url: str = Field(default="http://localhost:3000", alias="FRONTEND_URL")

    class Config:
        env_file = ".env"
        extra = "ignore"


class AuthConfig(BaseSettings):
    """Authentication configuration."""

    jwt_secret_key: str = Field(default="change-this-in-production", alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_expiration_hours: int = Field(default=24, alias="JWT_EXPIRATION_HOURS")

    class Config:
        env_file = ".env"
        extra = "ignore"


class LoggingConfig(BaseSettings):
    """Logging configuration."""

    level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_file: str = Field(default="logs/app.log", alias="LOG_FILE")
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    class Config:
        env_file = ".env"
        extra = "ignore"


class AppConfig(BaseSettings):
    """General application configuration."""

    name: str = Field(default="Smart English Test-Prep Agent", alias="APP_NAME")
    version: str = Field(default="1.0.0", alias="APP_VERSION")
    environment: str = Field(default="development", alias="ENVIRONMENT")

    class Config:
        env_file = ".env"
        extra = "ignore"


# Singleton instances
db_config = DatabaseConfig()
llm_config = LLMConfig()
test_config = TestConfig()
api_config = APIConfig()
auth_config = AuthConfig()
logging_config = LoggingConfig()
app_config = AppConfig()


class Config:
    """Main configuration class that aggregates all settings."""

    def __init__(self):
        self.db = db_config
        self.llm = llm_config
        self.test = test_config
        self.api = api_config
        self.auth = auth_config
        self.logging = logging_config
        self.app = app_config

    def validate(self) -> bool:
        """Validate that all required configuration is present."""
        errors = []

        if not self.llm.anthropic_api_key:
            errors.append("ANTHROPIC_API_KEY is required")

        if self.app.environment == "production":
            if self.auth.jwt_secret_key == "change-this-in-production":
                errors.append("JWT_SECRET_KEY must be changed in production")

        if errors:
            print("Configuration errors:")
            for error in errors:
                print(f"  - {error}")
            return False

        return True


# Global config instance
config = Config()


def get_config() -> Config:
    """Get the global configuration instance."""
    return config
