from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = "development"

    meta_app_id: str
    meta_app_secret: str
    meta_phone_number_id: str
    meta_whatsapp_token: str
    meta_webhook_verify_token: str
    meta_graph_api_version: str = "v23.0"

    squad_secret_key: str
    squad_base_url: str = "https://sandbox-api-d.squadco.com"
    squad_revenue_account: str
    squad_revenue_bank_code: str

    mono_public_key: str
    mono_secret_key: str
    mono_webhook_secret: str
    mono_base_url: str = "https://sandbox.mono.co"

    supabase_url: str
    supabase_key: str
    database_url: str

    upstash_redis_rest_url: str
    upstash_redis_rest_token: str

    groq_api_key: str
    admin_token: str
    secret_key: str

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
