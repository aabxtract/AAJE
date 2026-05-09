from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = "development"
    secret_key: str
    admin_token: str
    is_sandbox: bool = True

    # Twilio
    twilio_account_sid: str
    twilio_auth_token: str
    twilio_whatsapp_from: str

    # Mono
    mono_public_key: str
    mono_secret_key: str
    mono_webhook_secret: str
    mono_base_url: str = "https://api.withmono.com"

    # Squad
    squad_secret_key: str
    squad_base_url: str = "https://sandbox-api-d.squadco.com"
    squad_revenue_account: str

    # Supabase
    supabase_url: str
    supabase_key: str
    database_url: str

    # Upstash Redis
    upstash_redis_rest_url: str
    upstash_redis_rest_token: str

    # Groq
    groq_api_key: str

    # YarnGPT
    yarngpt_api_url: str
    yarngpt_api_key: str

    class Config:
        env_file = ".env"


settings = Settings()
