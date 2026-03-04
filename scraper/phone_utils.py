"""
Shared utilities for phone scrapers.

phone_utils.py
--------------
Provides a canonical name normaliser so that the same device scraped from
GSMArena and PhoneDB produces the same MongoDB document key, preventing
duplicate records.

Example collisions this fixes:
  GSMArena → "Samsung Galaxy S24 5G"
  PhoneDB  → "Samsung Galaxy S24"          ← same phone, different key

  GSMArena → "Apple iPhone 15 Pro Max"
  PhoneDB  → "Apple iPhone 15 Pro Max"     ← fine, already identical

  GSMArena → "Xiaomi Redmi Note 13 Pro+"
  PhoneDB  → "Xiaomi Redmi Note 13 Pro Plus" ← same phone, different key
"""

from __future__ import annotations

import re


# ---------------------------------------------------------------------------
# Token replacements applied in order (case-insensitive, full-word match)
# ---------------------------------------------------------------------------
_TOKEN_MAP: list[tuple[str, str]] = [
    # Suffix variants
    (r"\bpro\+",        "Pro Plus"),
    (r"\+",             " Plus"),       # standalone + at end of model names
    (r"\bplus\b",       "Plus"),
    (r"\bultra\b",      "Ultra"),
    (r"\bmax\b",        "Max"),
    (r"\bpro\b",        "Pro"),
    (r"\blite\b",       "Lite"),
    (r"\bse\b",         "SE"),
    (r"\bfe\b",         "FE"),          # Fan Edition
    (r"\bnfc\b",        ""),            # NFC suffix is noise for our purposes
    # Connectivity suffixes — strip these as they vary by region
    (r"\b5g\b",         ""),
    (r"\b4g\b",         ""),
    (r"\blte\b",        ""),
    # Dual-SIM and other noise suffixes
    (r"\bduos?\b",      ""),
    (r"\bdual\s+sim\b", ""),
    (r"\bdual\b",       ""),
]

# Compiled once at module load
_COMPILED_TOKENS: list[tuple[re.Pattern, str]] = [
    (re.compile(pattern, re.IGNORECASE), replacement)
    for pattern, replacement in _TOKEN_MAP
]

# Collapse any run of whitespace
_WHITESPACE_RE = re.compile(r"\s{2,}")


def normalise_phone_name(raw: str) -> str:
    """
    Return a canonical, whitespace-normalised phone name suitable for use
    as the MongoDB unique key.

    Steps:
    1. Strip leading/trailing whitespace.
    2. Apply token replacements (connectivity suffixes, symbol aliases).
    3. Collapse multiple spaces.
    4. Title-case the result for consistency.

    >>> normalise_phone_name("samsung galaxy s24 5g")
    'Samsung Galaxy S24'
    >>> normalise_phone_name("Xiaomi Redmi Note 13 Pro+")
    'Xiaomi Redmi Note 13 Pro Plus'
    >>> normalise_phone_name("OnePlus 12R 5G (NFC)")
    'OnePlus 12R'
    """
    name = raw.strip()

    # Remove parenthesised qualifiers like (NFC), (Global), (India) etc.
    name = re.sub(r"\(.*?\)", "", name)

    for pattern, replacement in _COMPILED_TOKENS:
        name = pattern.sub(replacement, name)

    # Collapse whitespace and title-case
    name = _WHITESPACE_RE.sub(" ", name).strip()
    return name.title()


def validate_phone_dict(phone: dict) -> list[str]:
    """
    Return a list of warning strings for a phone dict that has suspicious
    values.  The scrapers call this before upserting so problems are visible
    in the logs without crashing the run.

    Checks:
    - Required string fields are non-empty.
    - Numeric fields are non-negative.
    - OS is not 'Unknown'.
    - price == 0 is allowed (not all sources carry price) but logged.
    """
    warnings: list[str] = []
    name = phone.get("name", "")

    required_strings = ("name", "chipset", "os", "source")
    for field in required_strings:
        if not phone.get(field, "").strip():
            warnings.append(f"[{name}] '{field}' is empty")

    if phone.get("os", "Unknown") == "Unknown":
        warnings.append(f"[{name}] OS could not be detected")

    non_negative_ints = ("battery", "ram", "storage", "camera")
    for field in non_negative_ints:
        val = phone.get(field, -1)
        if val < 0:
            warnings.append(f"[{name}] '{field}' is negative ({val})")
        elif val == 0:
            warnings.append(f"[{name}] '{field}' is 0 — may be a parse miss")

    if phone.get("price", 0) == 0:
        warnings.append(f"[{name}] price is 0 — no pricing data found")

    return warnings