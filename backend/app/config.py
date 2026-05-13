from pathlib import Path

from pydantic_settings import BaseSettings


BASE_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    app_env: str = "development"
    app_public_url: str = ""
    frontend_url: str = ""
    whatsapp_bot_number: str = ""

    meta_app_id: str
    meta_app_secret: str
    meta_phone_number_id: str
    meta_whatsapp_token: str
    meta_webhook_verify_token: str
    meta_graph_api_version: str = "v23.0"
    meta_onboarding_profile_flow_id: str = ""
    meta_business_setup_flow_id: str = ""
    meta_pin_setup_flow_id: str = ""
    meta_pin_confirm_flow_id: str = ""
    meta_passport_flow_id: str = ""
    meta_flow_private_key: str = ""
    meta_flow_private_key_path: str = ""
    meta_flow_private_key_passphrase: str = ""

    squad_secret_key: str
    squad_base_url: str = "https://sandbox-api-d.squadco.com"
    squad_revenue_account: str
    squad_revenue_bank_code: str
    squad_mock_on_account_limit: bool = True

    mono_public_key: str
    mono_secret_key: str
    mono_webhook_secret: str
    mono_base_url: str = "https://sandbox.mono.co"
    mono_lookup_mock: bool = False

    supabase_url: str
    supabase_key: str
    database_url: str

    upstash_redis_rest_url: str
    upstash_redis_rest_token: str

    groq_api_key: str
    admin_token: str
    secret_key: str
    jwt_secret: str = ""
    jwt_algorithm: str = "HS256"
    jwt_expiry_hours: int = 168

    class Config:
        env_file = BASE_DIR / ".env"
        extra = "ignore"


settings = Settings()
