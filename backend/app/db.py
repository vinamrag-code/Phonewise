from typing import Any, Dict

from pymongo import MongoClient, ASCENDING

from .config import get_settings


settings = get_settings()

_client: MongoClient | None = None


def get_client() -> MongoClient:
    global _client
    if _client is None:
        _client = MongoClient(settings.mongo_uri)
    return _client


def get_db():
    return get_client()[settings.mongo_db]


def get_phones_collection():
    db = get_db()
    coll = db[settings.phones_collection]

    # Ensure some useful indexes
    coll.create_index([("name", ASCENDING)], unique=True)
    coll.create_index([("price", ASCENDING)])
    coll.create_index([("os", ASCENDING)])
    coll.create_index([("chipset", ASCENDING)])
    return coll


def upsert_phone(phone: Dict[str, Any]) -> None:
    """
    Upsert a phone document based on its unique name.
    """
    coll = get_phones_collection()
    coll.update_one({"name": phone["name"]}, {"$set": phone}, upsert=True)

