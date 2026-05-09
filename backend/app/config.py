from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Server
    APP_ENV: str = "development"
    SECRET_KEY: str
    ADMIN_TOKEN: str

    # Twilio
    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_WHATSAPP_FROM: str = "whatsapp:+14155238886"

    # Mono
    MONO_PUBLIC_KEY: str
    MONO_SECRET_KEY: str
    MONO_WEBHOOK_SECRET: str
    MONO_BASE_URL: str = "https://sandbox.mono.co"

    # Squad
    SQUAD_SECRET_KEY: str
    SQUAD_BASE_URL: str = "https://sandbox-api-d.squadco.com"
    SQUAD_REVENUE_ACCOUNT: str

    # Supabase
    SUPABASE_URL: str
    SUPABASE_KEY: str
    DATABASE_URL: str  # asyncpg DSN

    # Upstash Redis
    UPSTASH_REDIS_REST_URL: str
    UPSTASH_REDIS_REST_TOKEN: str

    # Groq
    GROQ_API_KEY: str

    # YarnGPT
    YARNGPT_API_URL: str
    YARNGPT_API_KEY: str


settings = Settings()
