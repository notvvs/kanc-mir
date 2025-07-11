from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    base_url: str = Field(default="https://kanc-mir.ru")

    mongo_url: str = Field(default="mongodb://localhost:27017/")
    db_name: str = Field(default="KancMir")
    collection_name: str = Field(default="products")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

settings = Settings()