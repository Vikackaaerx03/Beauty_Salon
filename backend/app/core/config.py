from functools import lru_cache
from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    MONGO_URI: str
    MONGO_DB_NAME: str = Field(validation_alias=AliasChoices("MONGO_DB_NAME", "DB_NAME"))
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

@lru_cache
def get_settings() -> Settings:
    return Settings()
settings = get_settings()
