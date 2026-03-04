"""
Scraper for PhoneDB (https://phonedb.net/)

This script:
- Fetches a list of devices from the PhoneDB "List all" page
- Visits each device's detailed specs page
- Extracts:
    - name
    - price (not available on PhoneDB, stored as 0.0)
    - battery (mAh)
    - ram (GB)
    - storage (GB)
    - camera (primary MP)
    - chipset (CPU)
    - os (Android/iOS/other)
- Upserts the data into MongoDB using backend.app.db.upsert_phone

It includes:
- Request delay
- Basic logging
- Error handling
- Duplicate checking via DB upsert
"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass
from typing import Dict, List, Optional

import requests
from bs4 import BeautifulSoup

# Import backend DB helper (requires running with PYTHONPATH set to project root)
from backend.app.db import upsert_phone  # type: ignore[import]


BASE_URL = "https://phonedb.net"
DEVICE_LIST_URL = f"{BASE_URL}/index.php?m=device&s=list"

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
    source: str = "phonedb.net"

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
    # Disable SSL certificate verification for PhoneDB scraping in local development
    # so that environments with broken CA bundles can still run the scraper.
    # Do NOT use this pattern for production-grade code that hits external APIs.
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
    Fetch a set of device detail URLs from the PhoneDB list page.
    Note: PhoneDB has many devices; we limit the number for practicality.
    """
    session = _create_session()
    logger.info("Fetching device list from %s", DEVICE_LIST_URL)

    resp = session.get(DEVICE_LIST_URL, timeout=20)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    links: List[str] = []
    seen = set()

    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "index.php" in href and "m=device" in href and "id=" in href:
            # Normalize to detailed specs URL
            if "d=detailed_specs" not in href:
                if "&" in href:
                    href = href + "&d=detailed_specs"
                else:
                    href = href + "&d=detailed_specs"
            url = _full_url(href)
            if url not in seen:
                seen.add(url)
                links.append(url)
        if len(links) >= max_devices:
            break

    logger.info("Discovered %d device links", len(links))
    return links


def _parse_mib_or_gib_to_gb(text: str) -> Optional[int]:
    """
    Convert strings like '4096 MiB RAM' or '8 GiB RAM' to integer GB.
    """
    text = text.replace(",", " ")
    mib_match = re.search(r"(\d+(?:\.\d+)?)\s*MiB", text, re.IGNORECASE)
    gib_match = re.search(r"(\d+(?:\.\d+)?)\s*GiB", text, re.IGNORECASE)

    if gib_match:
        val = float(gib_match.group(1))
        return max(1, int(round(val)))
    if mib_match:
        val = float(mib_match.group(1))
        gb = val / 1024.0
        return max(1, int(round(gb)))
    return None


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


def _parse_price_inr(specs: Dict[str, str]) -> float:
    """
    Try to extract an INR price from the specs table.

    PhoneDB exposes pricing information under the Geographical attributes
    section (e.g. "India: 14999 INR"). We look for that field first and
    fall back to scanning all values that mention INR/₹.
    """

    def _extract_amount(text: str) -> Optional[float]:
        m = re.search(r"(\d[\d,]*)\s*(?:inr|rs|₹)?", text, re.IGNORECASE)
        if not m:
            return None
        raw = m.group(1).replace(",", "")
        try:
            return float(raw)
        except ValueError:
            return None

    # Prefer explicit geographical / price related fields
    for key, value in specs.items():
        key_lower = key.lower()
        if "geographical" in key_lower or "price" in key_lower:
            amount = _extract_amount(value)
            if amount is not None:
                return amount

    # Fallback: scan all values mentioning INR/₹
    for value in specs.values():
        if "inr" in value.lower() or "₹" in value:
            amount = _extract_amount(value)
            if amount is not None:
                return amount

    return 0.0


def _detect_os(platform_text: str, os_text: str | None = None) -> str:
    combined = " ".join(filter(None, [platform_text or "", os_text or ""])).lower()
    if "android" in combined:
        return "Android"
    if "ios" in combined or "ipad" in combined or "iphone" in combined:
        return "iOS"
    if "windows" in combined:
        return "Windows"
    if platform_text:
        return platform_text.split()[0]
    return "Unknown"


def parse_device_page(html: str) -> ScrapedPhone | None:
    soup = BeautifulSoup(html, "html.parser")

    # Build a mapping from spec row label -> value
    specs: Dict[str, str] = {}
    for table in soup.find_all("table"):
        for row in table.find_all("tr"):
            cells = row.find_all(["th", "td"])
            if len(cells) < 2:
                continue
            key = cells[0].get_text(" ", strip=True)
            value = cells[1].get_text(" ", strip=True)
            if key and value:
                specs[key] = value

    # Name
    name = specs.get("Model")
    if not name:
        # Fallback to title
        h1 = soup.find("h1")
        name = h1.get_text(" ", strip=True) if h1 else None
    if not name:
        logger.warning("Could not determine model name from page")
        return None

    # OS / Platform
    platform = specs.get("Platform", "")
    os_detail = specs.get("Operating System", "")
    os_name = _detect_os(platform, os_detail)

    # Chipset / CPU
    chipset = specs.get("CPU", "").strip()

    # RAM & storage
    ram_gb = _parse_mib_or_gib_to_gb(specs.get("RAM Capacity", ""))
    if ram_gb is None:
        ram_gb = 0

    storage_gb = _parse_mib_or_gib_to_gb(specs.get("Non-volatile Memory Capacity", ""))
    if storage_gb is None:
        storage_gb = 0

    # Camera (primary MP)
    camera_mp = _parse_camera_mp(specs.get("Number of effective pixels", ""))
    if camera_mp is None:
        camera_mp = 0

    # Battery
    battery_mah = _parse_battery_mah(specs.get("Nominal Battery Capacity", ""))
    if battery_mah is None:
        battery_mah = 0

    price = _parse_price_inr(specs)

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
    Main entrypoint used by the backend (/update-database) and for manual runs.

    Returns:
        Number of successfully upserted phone records.
    """
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    session = _create_session()
    links = fetch_device_links(max_devices=max_devices)
    logger.info("Starting scrape of up to %d devices", len(links))

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

    logger.info("Scraper finished. Upserted %d devices.", success_count)
    return success_count


if __name__ == "__main__":
    # Allow running as: PYTHONPATH=. python -m scraper.scrape_phones
    run_scraper()

