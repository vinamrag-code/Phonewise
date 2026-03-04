from __future__ import annotations

from typing import Any, Dict, List, Tuple

from .models import (
    PhoneInDB,
    PhoneRecommendation,
    PreferenceWeights,
    RecommendationReason,
    PhoneTag,
)


def _normalize_range(value: float, min_v: float, max_v: float) -> float:
    if max_v == min_v:
        return 0.5
    return (value - min_v) / (max_v - min_v)


def _compute_feature_ranges(phones: List[Dict[str, Any]]) -> Dict[str, Tuple[float, float]]:
    keys = ["price", "battery", "ram", "storage", "camera"]
    ranges: Dict[str, Tuple[float, float]] = {}
    for key in keys:
        vals = [float(p.get(key, 0)) for p in phones if p.get(key) is not None]
        if not vals:
            ranges[key] = (0.0, 1.0)
        else:
            ranges[key] = (min(vals), max(vals))
    return ranges


def score_phone(
    phone: Dict[str, Any],
    weights: PreferenceWeights,
    ranges: Dict[str, Tuple[float, float]],
    max_budget: float | None,
    primary_use: str | None,
) -> Tuple[float, Dict[str, float]]:
    weights = weights.normalized()
    feature_scores: Dict[str, float] = {}

    # Budget: higher score when price is below or near budget
    price = float(phone.get("price") or 0)
    if max_budget:
        if price > max_budget * 1.3:
            budget_score = 0.0
        else:
            budget_score = 1.0 - min(price / max_budget, 1.2) * 0.8
    else:
        min_p, max_p = ranges["price"]
        budget_score = 1.0 - _normalize_range(price, min_p, max_p)
    feature_scores["budget"] = max(0.0, min(1.0, budget_score))

    # Higher is better for these metrics
    min_b, max_b = ranges["battery"]
    feature_scores["battery"] = _normalize_range(float(phone.get("battery") or 0), min_b, max_b)

    min_c, max_c = ranges["camera"]
    feature_scores["camera"] = _normalize_range(float(phone.get("camera") or 0), min_c, max_c)

    min_r, max_r = ranges["ram"]
    feature_scores["ram"] = _normalize_range(float(phone.get("ram") or 0), min_r, max_r)

    min_s, max_s = ranges["storage"]
    feature_scores["storage"] = _normalize_range(float(phone.get("storage") or 0), min_s, max_s)

    # Performance proxy: derive a simple score from chipset + RAM
    chipset_str = (phone.get("chipset") or "").lower()
    perf_base = 0.4
    gaming_keywords = ["snapdragon 8", "snapdragon 7", "dimensity 9", "a17", "a16"]
    mid_keywords = ["snapdragon 6", "dimensity 8", "a15", "a14"]
    for kw in gaming_keywords:
        if kw in chipset_str:
            perf_base = 0.95
            break
    else:
        for kw in mid_keywords:
            if kw in chipset_str:
                perf_base = 0.7
                break
    perf_score = min(1.0, perf_base + feature_scores["ram"] * 0.2)

    # Slightly favor performance when primary use is gaming
    if primary_use and primary_use.lower() == "gaming":
        perf_score = min(1.0, perf_score * 1.05)

    feature_scores["performance"] = perf_score

    score = (
        weights.budget * feature_scores["budget"]
        + weights.camera * feature_scores["camera"]
        + weights.battery * feature_scores["battery"]
        + weights.performance * feature_scores["performance"]
        + weights.storage * feature_scores["storage"]
        + weights.ram * feature_scores["ram"]
    )

    return score, feature_scores


def build_tags(phone: Dict[str, Any], feature_scores: Dict[str, float], primary_use: str | None) -> List[PhoneTag]:
    tags: List[PhoneTag] = []
    if feature_scores.get("performance", 0) > 0.8:
        tags.append(PhoneTag(key="gaming", label="Great for gaming"))
    if feature_scores.get("battery", 0) > 0.8:
        tags.append(PhoneTag(key="battery", label="Exceptional battery life"))
    if feature_scores.get("camera", 0) > 0.8:
        tags.append(PhoneTag(key="camera", label="Excellent camera"))
    if feature_scores.get("budget", 0) > 0.8:
        tags.append(PhoneTag(key="budget", label="Great value"))
    if primary_use and primary_use.lower() == "photography" and feature_scores.get("camera", 0) > 0.7:
        tags.append(PhoneTag(key="photo", label="Ideal for photography"))
    return tags


def build_reasons(
    phone: Dict[str, Any],
    score: float,
    feature_scores: Dict[str, float],
    max_budget: float | None,
    primary_use: str | None,
) -> List[RecommendationReason]:
    reasons: List[RecommendationReason] = []

    if max_budget is not None and phone.get("price") is not None:
        if phone["price"] <= max_budget:
            reasons.append(
                RecommendationReason(
                    title="Fits your budget",
                    detail=f"Priced at {phone['price']:.0f}, which is within your budget of {max_budget:.0f}.",
                )
            )
        elif feature_scores.get("budget", 0) > 0.6:
            reasons.append(
                RecommendationReason(
                    title="Strong value",
                    detail="Offers strong overall specs for the price compared to other options.",
                )
            )

    if feature_scores.get("camera", 0) > 0.7:
        reasons.append(
            RecommendationReason(
                title="Great camera",
                detail=f"Camera score is above most phones in this range (camera rating {phone.get('camera')}).",
            )
        )

    if feature_scores.get("battery", 0) > 0.7:
        reasons.append(
            RecommendationReason(
                title="Long battery life",
                detail=f"Battery capacity of {phone.get('battery')} mAh should comfortably last a full day of heavy use.",
            )
        )

    if feature_scores.get("performance", 0) > 0.7:
        if primary_use and primary_use.lower() == "gaming":
            reasons.append(
                RecommendationReason(
                    title="Gaming-ready performance",
                    detail="Chipset and RAM combination is well-suited for gaming and heavy multitasking.",
                )
            )
        else:
            reasons.append(
                RecommendationReason(
                    title="Smooth performance",
                    detail="Expect smooth day-to-day performance thanks to the capable chipset and RAM.",
                )
            )

    if not reasons:
        reasons.append(
            RecommendationReason(
                title="Balanced choice",
                detail="Offers a balanced mix of performance, camera, and battery for your needs.",
            )
        )

    reasons.append(
        RecommendationReason(
            title="Overall match score",
            detail=f"This phone achieves an overall match score of {int(score * 100)}% based on your preferences.",
        )
    )

    return reasons


def recommend_phones(
    phones: List[Dict[str, Any]],
    weights: PreferenceWeights,
    max_budget: float | None = None,
    min_ram: int | None = None,
    min_storage: int | None = None,
    os_preference: str | None = None,
    primary_use: str | None = None,
    limit: int = 10,
) -> List[PhoneRecommendation]:
    # Filter first by hard constraints
    filtered: List[Dict[str, Any]] = []
    for p in phones:
        if min_ram is not None and int(p.get("ram") or 0) < min_ram:
            continue
        if min_storage is not None and int(p.get("storage") or 0) < min_storage:
            continue
        if os_preference and p.get("os") and p["os"].lower() != os_preference.lower():
            continue
        filtered.append(p)

    if not filtered:
        return []

    ranges = _compute_feature_ranges(filtered)
    scored: List[Tuple[Dict[str, Any], float, Dict[str, float]]] = []

    for phone in filtered:
        s, feature_scores = score_phone(phone, weights, ranges, max_budget, primary_use)
        scored.append((phone, s, feature_scores))

    scored.sort(key=lambda x: x[1], reverse=True)

    recommendations: List[PhoneRecommendation] = []
    top_scored = scored[:limit]

    # Normalize final scores into 0-100 range relative to best/worst selected
    scores_only = [s for _, s, _ in top_scored]
    min_s, max_s = min(scores_only), max(scores_only)

    for phone_doc, s, feature_scores in top_scored:
        if max_s == min_s:
            percentage = 85
        else:
            percentage = int(60 + 40 * (s - min_s) / (max_s - min_s))

        reasons = build_reasons(phone_doc, s, feature_scores, max_budget, primary_use)
        tags = build_tags(phone_doc, feature_scores, primary_use)

        phone_model = PhoneInDB(
            id=str(phone_doc.get("_id")) if phone_doc.get("_id") else None,
            name=phone_doc["name"],
            price=float(phone_doc.get("price") or 0),
            battery=int(phone_doc.get("battery") or 0),
            ram=int(phone_doc.get("ram") or 0),
            storage=int(phone_doc.get("storage") or 0),
            camera=int(phone_doc.get("camera") or 0),
            chipset=phone_doc.get("chipset") or "",
            os=phone_doc.get("os") or "",
        )

        recommendations.append(
            PhoneRecommendation(
                phone=phone_model,
                match_score=s,
                match_percentage=percentage,
                reasons=reasons,
                tags=tags,
            )
        )

    return recommendations

