from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    debug: bool = False
    app_name: str = "Wydarzenia API"

    class Config:
        env_file = ".env"


settings = Settings()
