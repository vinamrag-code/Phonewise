from typing import Any, Dict, List

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .db import get_phones_collection
from .models import (
    PhoneInDB,
    RecommendationRequest,
    RecommendationResponse,
)
from .recommendation import recommend_phones

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="Backend API for the Smart Phone Recommendation web application.",
    version="1.0.0",
)

# Basic CORS setup for local dev (frontend on Vite default port 5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Simple in-memory cache for recommendation requests
_recommendation_cache: Dict[str, Dict[str, Any]] = {}
CACHE_TTL_SECONDS = 300

import time
import hashlib
import json


def _cache_key_from_payload(payload: Dict[str, Any]) -> str:
    serialized = json.dumps(payload, sort_keys=True)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _get_cached_recommendations(key: str) -> RecommendationResponse | None:
    item = _recommendation_cache.get(key)
    if not item:
        return None
    if time.time() - item["time"] > CACHE_TTL_SECONDS:
        _recommendation_cache.pop(key, None)
        return None
    return item["value"]


def _set_cached_recommendations(key: str, value: RecommendationResponse) -> None:
    _recommendation_cache[key] = {"value": value, "time": time.time()}


@app.get("/phones", response_model=List[PhoneInDB])
def list_phones(
    os: str | None = Query(default=None, description="Filter by OS, e.g. Android or iOS"),
    max_price: float | None = Query(default=None, description="Optional upper bound on price"),
):
    coll = get_phones_collection()
    query: Dict[str, Any] = {}
    if os:
        query["os"] = os
    if max_price is not None:
        query["price"] = {"$lte": max_price}
    docs = list(coll.find(query))
    return [
        PhoneInDB(
            id=str(d.get("_id")) if d.get("_id") else None,
            name=d["name"],
            price=float(d.get("price") or 0),
            battery=int(d.get("battery") or 0),
            ram=int(d.get("ram") or 0),
            storage=int(d.get("storage") or 0),
            camera=int(d.get("camera") or 0),
            chipset=d.get("chipset") or "",
            os=d.get("os") or "",
        )
        for d in docs
    ]


@app.post("/recommend", response_model=RecommendationResponse)
def recommend(request: RecommendationRequest):
    payload = request.model_dump()
    cache_key = _cache_key_from_payload(payload)
    cached = _get_cached_recommendations(cache_key)
    if cached:
        return cached

    coll = get_phones_collection()
    phones = list(coll.find({}))
    if not phones:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No phone data available. Please run the scraper to populate the database.",
        )

    weights = request.weights or None
    if weights is None:
        # Adjust defaults based on primary use if not explicitly provided
        from .models import PreferenceWeights

        if request.primary_use and request.primary_use.lower() == "gaming":
            weights = PreferenceWeights(
                budget=0.2,
                camera=0.15,
                battery=0.2,
                performance=0.35,
                storage=0.05,
                ram=0.05,
            )
        elif request.primary_use and request.primary_use.lower() == "photography":
            weights = PreferenceWeights(
                budget=0.2,
                camera=0.4,
                battery=0.15,
                performance=0.15,
                storage=0.05,
                ram=0.05,
            )
        else:
            weights = PreferenceWeights()

    recs = recommend_phones(
        phones=phones,
        weights=weights,
        max_budget=request.max_budget,
        min_ram=request.min_ram,
        min_storage=request.min_storage,
        os_preference=request.os_preference,
        primary_use=request.primary_use,
        limit=10,
    )

    response = RecommendationResponse(recommendations=recs)
    _set_cached_recommendations(cache_key, response)
    return response


@app.post("/update-database")
def update_database(api_token: str = Query(..., description="Simple shared secret for admin operations")):
    """
    Triggers a scraper run to refresh the phones collection.
    In production, you should protect this endpoint with proper authentication.
    """
    if api_token != settings.api_secret_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API token")

    try:
        # Import here to avoid circular dependencies
        from scraper.scrape_phones import run_scraper

        count = run_scraper()
    except ImportError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Scraper module not available: {e}",
        )
    except Exception as e:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Scraper failed: {e}",
        )

    # Clear cache after DB update
    _recommendation_cache.clear()

    return {"status": "ok", "updated_count": count}


@app.get("/health")
def health_check():
    return {"status": "ok", "service": settings.app_name}

