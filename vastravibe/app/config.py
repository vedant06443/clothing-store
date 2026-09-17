from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )

    # App
    APP_NAME: str = "Suyog Collection"
    APP_ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "suyog-collection-secret-key-change-in-production-min-32"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days

    # Database
    DATABASE_URL: str = "sqlite:///./vastravibe.db"

    # Razorpay
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""

    # Cloudinary
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""

    # Admin defaults
    ADMIN_EMAIL: str = "admin@vastravibe.com"
    ADMIN_PASSWORD: str = "Admin@12345"


settings = Settings()
