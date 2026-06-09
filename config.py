from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    jwt_secret_key: str
    access_token_expire_minutes: int = 30
    debug: bool = False
    app_name: str = "Wydarzenia API"

    class Config:
        env_file = ".env"


settings = Settings()
