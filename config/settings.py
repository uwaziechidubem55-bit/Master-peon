from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    database_url: str = "postgresql://master:master@db:5432/masterpeon"
    secret_key: str = "change-me"
    admin_username: str = "change-me"
    admin_password: str = "change-me"
    admin_secret_path: str = "/.x"
    llm_api_key: str = ""
    llm_model: str = "gemini-2.5-flash"
    llm_endpoint: str = "https://googleapis.com"
    flw_public_key: str = ""
    flw_secret_key: str = ""
    flw_webhook_hash: str = ""
    flw_forward_token: str = ""
    flw_bank_code: str = ""
    flw_account_number: str = ""
    base_url: str = "http://localhost:8000"
    upload_base_url: str = ""
    selfies_dir: str = "/app/data/selfies"

    tier_limits: dict = {
        "free":   {"chats": 5,  "tools": ["nmap", "nikto", "tcpdump"], "tool_calls": 5,  "price_month": 0,  "price_year": 0},
        "pro":    {"chats": 50, "tools": ["nmap", "nikto", "tcpdump", "hydra", "john"], "tool_calls": 50, "price_month": 19, "price_year": 190},
        "advance":{"chats": 150, "tools": ["nmap", "nikto", "tcpdump", "hydra", "john", "sqlmap", "dirb", "ffuf"], "tool_calls": 150, "price_month": 35, "price_year": 350},
        "master": {"chats": 0,  "tools": ["ALL"], "tool_calls": 0, "price_month": 50, "price_year": 500},
    }

settings = Settings()