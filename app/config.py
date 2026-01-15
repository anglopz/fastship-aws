from pydantic_settings import BaseSettings, SettingsConfigDict  # type: ignore


_base_config = SettingsConfigDict(
    env_file="./.env",
    env_ignore_empty=True,
    extra="ignore",
)


class AppSettings(BaseSettings):
    """Application settings"""
    APP_NAME: str = "FastShip"
    APP_DOMAIN: str = "localhost:8000"
    FRONTEND_URL: str = "http://localhost:5173"  # Frontend URL for redirects

    model_config = _base_config


class SecuritySettings(BaseSettings):
    JWT_SECRET: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"

    model_config = _base_config


class DatabaseSettings(BaseSettings):
    # Support both DATABASE_URL (from Render) and individual POSTGRES_* settings
    DATABASE_URL: str = ""
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_DB: str = "fastapi_db"
    
    # Support both REDIS_URL (from Render) and individual REDIS_* settings
    REDIS_URL: str = ""
    REDIS_HOST: str = "localhost"
    REDIS_PORT: str = "6379"

    model_config = _base_config

    @property
    def POSTGRES_URL(self) -> str:
        """Return a Postgres async URL.
        
        Prioritizes DATABASE_URL if provided (e.g., from Render).
        Otherwise builds from individual POSTGRES_* settings.
        Converts postgresql:// to postgresql+asyncpg:// if needed.
        """
        if self.DATABASE_URL:
            # Convert postgresql:// to postgresql+asyncpg:// if needed
            if self.DATABASE_URL.startswith("postgresql://"):
                return self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
            elif self.DATABASE_URL.startswith("postgresql+asyncpg://"):
                return self.DATABASE_URL
            else:
                # Already in correct format or needs conversion
                return self.DATABASE_URL
        
        # Build from individual settings
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )
    
    def get_redis_connection_params(self) -> dict:
        """Get Redis connection parameters.
        
        Prioritizes REDIS_URL if provided (e.g., from Render).
        Otherwise uses individual REDIS_HOST/REDIS_PORT settings.
        
        Returns:
            dict with 'host', 'port', and optionally 'url' keys
        """
        if self.REDIS_URL:
            # Parse REDIS_URL (format: redis://host:port/db)
            from urllib.parse import urlparse
            parsed = urlparse(self.REDIS_URL)
            return {
                "url": self.REDIS_URL,
                "host": parsed.hostname or "localhost",
                "port": parsed.port or 6379,
                "db": int(parsed.path.lstrip("/")) if parsed.path else 1,
            }
        
        # Use individual settings
        return {
            "host": self.REDIS_HOST,
            "port": int(self.REDIS_PORT),
            "db": 1,
        }


class MailSettings(BaseSettings):
    """Mail/Email notification settings"""
    EMAIL_MODE: str = "sandbox"  # "sandbox" for Mailtrap, "production" for real SMTP
    MAIL_USERNAME: str = ""
    MAIL_PASSWORD: str = ""
    MAIL_FROM: str = "noreply@example.com"
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_FROM_NAME: str = "FastShip"
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    USE_CREDENTIALS: bool = True
    VALIDATE_CERTS: bool = True
    
    # Mailtrap settings (used when EMAIL_MODE=sandbox)
    MAILTRAP_USERNAME: str = ""
    MAILTRAP_PASSWORD: str = ""
    MAILTRAP_SERVER: str = "sandbox.smtp.mailtrap.io"
    MAILTRAP_PORT: int = 587

    model_config = _base_config
    
    def get_smtp_config(self) -> dict:
        """
        Get SMTP configuration based on EMAIL_MODE.
        
        Returns:
            Dictionary with SMTP settings (server, port, username, password)
        """
        if self.EMAIL_MODE.lower() == "sandbox":
            # Use Mailtrap for testing
            return {
                "MAIL_SERVER": self.MAILTRAP_SERVER,
                "MAIL_PORT": self.MAILTRAP_PORT,
                "MAIL_USERNAME": self.MAILTRAP_USERNAME or self.MAIL_USERNAME,
                "MAIL_PASSWORD": self.MAILTRAP_PASSWORD or self.MAIL_PASSWORD,
            }
        else:
            # Use production SMTP
            return {
                "MAIL_SERVER": self.MAIL_SERVER,
                "MAIL_PORT": self.MAIL_PORT,
                "MAIL_USERNAME": self.MAIL_USERNAME,
                "MAIL_PASSWORD": self.MAIL_PASSWORD,
            }


class TwilioSettings(BaseSettings):
    """Twilio SMS notification settings"""
    TWILIO_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_NUMBER: str = ""

    model_config = _base_config


class LoggingSettings(BaseSettings):
    """Logging configuration settings"""
    LOG_FILE: str = "file.log"
    LOG_DIR: str = "logs"
    ENABLE_REQUEST_LOGGING: bool = True
    LOG_LEVEL: str = "INFO"

    model_config = _base_config


class CORSSettings(BaseSettings):
    """CORS configuration settings"""
    # Comma-separated list of allowed origins
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173,http://localhost:5174,http://127.0.0.1:3000,http://127.0.0.1:5173"
    
    @property
    def allowed_origins(self) -> list[str]:
        """Parse CORS_ORIGINS string into a list"""
        if not self.CORS_ORIGINS:
            return []
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    model_config = _base_config


# New naming convention (db_settings, security_settings)
app_settings = AppSettings()
db_settings = DatabaseSettings()
security_settings = SecuritySettings()
mail_settings = MailSettings()
twilio_settings = TwilioSettings()
logging_settings = LoggingSettings()
cors_settings = CORSSettings()

# Migration wrapper for backward compatibility
# TODO: Remove this after all code is migrated to use db_settings
settings = db_settings
