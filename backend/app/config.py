import os
from functools import lru_cache

from pydantic import BaseModel
from dotenv import load_dotenv


load_dotenv()


class Settings(BaseModel):
    app_name: str = "Smart Phone Recommender API"
    mongo_uri: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    mongo_db: str = os.getenv("MONGO_DB", "phone_recommender")
    phones_collection: str = os.getenv("PHONES_COLLECTION", "phones")
    api_secret_token: str = os.getenv("API_SECRET_TOKEN", "change-me")  # for simple admin protection


@lru_cache
def get_settings() -> Settings:
    return Settings()

