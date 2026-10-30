from pydantic_settings import BaseSettings, SettingsConfigDict

class APISettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    
    api_admin_user: str = "admin"
    api_admin_password: str = "admin_api_secret"
    jwt_secret_key: str = "super_secret_jwt_key_change_in_production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Credenciales de BD para la API (Principio de Menor Privilegio)
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "maritime"
    api_user: str = "api_user"
    api_user_password: str = "api_dev_only"

    @property
    def database_url(self) -> str:
        return f"postgresql+psycopg://{self.api_user}:{self.api_user_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

settings = APISettings()
