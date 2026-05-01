from dotenv import load_dotenv
import os

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    MONGO_URI: str
    app_name: str = "Phonewise API" 
    MONGO_DB: str = "phone_recommender"
    PHONES_COLLECTION: str = "phones"
    API_SECRET_TOKEN: str = "change-me"

def get_settings():
    return Settings()
