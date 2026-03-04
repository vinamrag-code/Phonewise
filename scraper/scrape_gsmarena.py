"""
Scraper for GSMArena (https://www.gsmarena.com/)

This script:
- Fetches device links from a small set of GSMArena brand pages
- Visits each device's detailed specs page
- Extracts:
    - name
    - price (numeric if present)
    - battery (mAh)
    - ram (GB)
    - storage (GB)
    - camera (primary MP)
    - chipset (CPU)
    - os (Android/iOS/other)
- Upserts the data into MongoDB using backend.app.db.upsert_phone

Run as:
    PYTHONPATH=. python -m scraper.scrape_gsmarena
"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass
from typing import Dict, List, Optional

import requests
from bs4 import BeautifulSoup

from backend.app.db import upsert_phone  # type: ignore[import]


BASE_URL = "https://www.gsmarena.com"

# A small set of popular brand listing pages to keep this manageable.
BRAND_LIST_URLS = [
    f"{BASE_URL}/samsung-phones-9.php",
    f"{BASE_URL}/xiaomi-phones-80.php",
    f"{BASE_URL}/realme-phones-118.php",
    f"{BASE_URL}/oneplus-phones-95.php",
    f"{BASE_URL}/apple-phones-48.php",
]

REQUEST_DELAY_SECONDS = 1.5
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)


logger = logging.getLogger(__name__)


@dataclass
class ScrapedPhone:
    name: str
    price: float
    battery: int
    ram: int
    storage: int
    camera: int
    chipset: str
    os: str
    country: str = "India"
    currency: str = "INR"
    source: str = "gsmarena.com"

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "price": self.price,
            "battery": self.battery,
            "ram": self.ram,
            "storage": self.storage,
            "camera": self.camera,
            "chipset": self.chipset,
            "os": self.os,
            "country": self.country,
            "currency": self.currency,
            "source": self.source,
        }


def _create_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": USER_AGENT})
    # Disable SSL verification in local dev to avoid CA issues.
    s.verify = False
    return s


def _full_url(href: str) -> str:
    if href.startswith("http"):
        return href
    if href.startswith("/"):
        return BASE_URL + href
    return f"{BASE_URL}/{href.lstrip('/')}"


def fetch_device_links(max_devices: int = 150) -> List[str]:
    """
    Collect device detail URLs from a handful of GSMArena brand pages.
    """
    session = _create_session()
    links: List[str] = []
    seen: set[str] = set()

    for list_url in BRAND_LIST_URLS:
        if len(links) >= max_devices:
            break

        logger.info("Fetching brand list from %s", list_url)
        resp = session.get(list_url, timeout=20)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")

        # Device links are usually within .makers ul li a
        for a in soup.select(".makers a[href]"):
            href = a["href"]
            if not href.endswith(".php"):
                continue
            url = _full_url(href)
            if url in seen:
                continue
            seen.add(url)
            links.append(url)
            if len(links) >= max_devices:
                break

        time.sleep(REQUEST_DELAY_SECONDS)

    logger.info("Discovered %d GSMArena device links", len(links))
    return links


def _parse_specs_table(html: str) -> Dict[str, str]:
    """
    Build a mapping from spec row label -> value from GSMArena's specs table.

    GSMArena markup changes from time to time; to be robust we:
    - Prefer the main specs container with id="specs-list"
    - Fall back to scanning all tables on the page
    - Accept rows even if classes are slightly different
    """
    soup = BeautifulSoup(html, "html.parser")
    specs: Dict[str, str] = {}

    root = soup.find(id="specs-list") or soup

    for table in root.find_all("table"):
        for row in table.find_all("tr"):
            th = row.find("th", class_="ttl") or row.find("th")
            td = row.find("td", class_="nfo") or row.find("td")
            if not th or not td:
                continue
            key = th.get_text(" ", strip=True)
            value = td.get_text(" ", strip=True)
            if key and value:
                specs[key] = value
    return specs


def _parse_battery_mah(text: str) -> Optional[int]:
    m = re.search(r"(\d+(?:\.\d+)?)\s*mAh", text, re.IGNORECASE)
    if not m:
        return None
    return int(round(float(m.group(1))))


def _parse_camera_mp(text: str) -> Optional[int]:
    m = re.search(r"(\d+(?:\.\d+)?)\s*MP", text, re.IGNORECASE)
    if not m:
        return None
    return int(round(float(m.group(1))))


def _find_battery_mah(specs: Dict[str, str]) -> int:
    """
    Find a battery capacity in mAh by scanning all spec values.
    """
    # Prefer keys that look battery-related
    for key, value in specs.items():
        if "battery" in key.lower() or "type" in key.lower() or "charging" in key.lower():
            mah = _parse_battery_mah(value)
            if mah is not None:
                return mah

    # Fallback: scan every value
    for value in specs.values():
        mah = _parse_battery_mah(value)
        if mah is not None:
            return mah

    return 0


def _find_camera_mp(specs: Dict[str, str]) -> int:
    """
    Find a main camera megapixel value by scanning camera-related rows.
    """
    camera_keys = {"single", "dual", "triple", "quad", "main camera", "camera"}

    for key, value in specs.items():
        key_lower = key.lower()
        if any(k in key_lower for k in camera_keys):
            mp = _parse_camera_mp(value)
            if mp is not None:
                return mp

    # Fallback: scan all values
    for value in specs.values():
        mp = _parse_camera_mp(value)
        if mp is not None:
            return mp

    return 0


def _parse_ram_and_storage(text: str) -> tuple[int, int]:
    """
    Parse a string like '128GB 8GB RAM' into (ram_gb, storage_gb).
    """
    ram_gb = 0
    storage_gb = 0

    ram_match = re.search(r"(\d+)\s*GB\s*RAM", text, re.IGNORECASE)
    if ram_match:
        ram_gb = int(ram_match.group(1))

    # Storage is usually the first GB number before RAM
    storage_match = re.search(r"(\d+)\s*GB", text, re.IGNORECASE)
    if storage_match:
        storage_gb = int(storage_match.group(1))

    return ram_gb, storage_gb


def _detect_os(os_text: str) -> str:
    t = (os_text or "").lower()
    if "android" in t:
        return "Android"
    if "ios" in t or "ipad" in t or "iphone" in t:
        return "iOS"
    if "windows" in t:
        return "Windows"
    return os_text.split()[0] if os_text else "Unknown"


def _parse_price(specs: Dict[str, str]) -> float:
    """
    Try to extract a numeric price from specs, preferring fields mentioning price.
    """

    def _extract_amount(text: str) -> Optional[float]:
        m = re.search(r"(\d[\d,]*)", text)
        if not m:
            return None
        raw = m.group(1).replace(",", "")
        try:
            return float(raw)
        except ValueError:
            return None

    # GSMArena usually has a "Price" row under Misc
    for key, value in specs.items():
        if "price" in key.lower():
            amount = _extract_amount(value)
            if amount is not None:
                return amount

    # Fallback: scan all values looking for a number
    for value in specs.values():
        amount = _extract_amount(value)
        if amount is not None:
            return amount

    return 0.0


def parse_device_page(html: str) -> ScrapedPhone | None:
    soup = BeautifulSoup(html, "html.parser")

    # Name
    name_elt = soup.find("h1", class_="specs-phone-name-title")
    name = name_elt.get_text(" ", strip=True) if name_elt else None
    if not name:
        logger.warning("Could not determine model name from page")
        return None

    specs = _parse_specs_table(html)

    # OS / Platform
    os_text = specs.get("OS", "")
    os_name = _detect_os(os_text)

    # Chipset / CPU
    chipset = specs.get("Chipset", "").strip()

    # Memory (RAM & storage)
    mem_text = specs.get("Internal", "") or specs.get("Memory", "")
    ram_gb, storage_gb = _parse_ram_and_storage(mem_text)

    # Camera (main MP)
    camera_mp = _find_camera_mp(specs)

    # Battery
    battery_mah = _find_battery_mah(specs)

    price = _parse_price(specs)

    return ScrapedPhone(
        name=name,
        price=price,
        battery=battery_mah,
        ram=ram_gb,
        storage=storage_gb,
        camera=camera_mp,
        chipset=chipset,
        os=os_name,
    )


def run_scraper(max_devices: int = 150) -> int:
    """
    Main entrypoint for scraping GSMArena.

    Returns:
        Number of successfully upserted phone records.
    """
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    session = _create_session()
    links = fetch_device_links(max_devices=max_devices)
    logger.info("Starting GSMArena scrape of up to %d devices", len(links))

    success_count = 0

    for idx, url in enumerate(links, start=1):
        try:
            logger.info("Fetching device %d/%d: %s", idx, len(links), url)
            resp = session.get(url, timeout=25)
            resp.raise_for_status()

            phone = parse_device_page(resp.text)
            if not phone:
                logger.warning("Skipping device %s due to parse failure", url)
                continue

            upsert_phone(phone.to_dict())
            success_count += 1
        except Exception as exc:  # noqa: BLE001
            logger.exception("Error while processing %s: %s", url, exc)
        finally:
            time.sleep(REQUEST_DELAY_SECONDS)

    logger.info("GSMArena scraper finished. Upserted %d devices.", success_count)
    return success_count


if __name__ == "__main__":
    # Allow running as: PYTHONPATH=. python -m scraper.scrape_gsmarena
    run_scraper()

