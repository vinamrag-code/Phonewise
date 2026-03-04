"""
Scraper for PhoneDB (https://phonedb.net/)

This script:
- Fetches a list of devices from the PhoneDB "List all" page
- Visits each device's detailed specs page
- Extracts:
    - name
    - price (INR if available, else 0.0)
    - battery (mAh)
    - ram (GB)
    - storage (GB)
    - camera (primary MP)
    - chipset (CPU)
    - os (Android/iOS/other)
- Upserts the data into MongoDB using backend.app.db.upsert_phone
"""

from __future__ import annotations

import logging
import re
import ssl
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import requests
from bs4 import BeautifulSoup

from backend.app.db import upsert_phone  # type: ignore[import]
from scraper.phone_utils import normalise_phone_name, validate_phone_dict  # type: ignore[import]


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
    """
    Create a requests Session with SSL verification disabled for phonedb.net.

    phonedb.net serves a certificate whose issuer is not in many system CA
    bundles (common on Linux with a minimal cert store). We disable
    verification at the session level and suppress the urllib3
    InsecureRequestWarning so logs stay clean.

    FIX: The previous _TLSAdapter approach set verify=False inside send()
    AFTER requests had already applied its own verify logic, so the SSL
    error was never actually suppressed. Setting s.verify = False directly
    on the session is the correct and reliable approach.
    """
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    s = requests.Session()
    s.headers.update({
        "User-Agent": USER_AGENT,
        "Accept-Language": "en-US,en;q=0.9",
    })
    s.verify = False  # phonedb.net has a broken CA chain on many Linux systems
    return s


def _full_url(href: str) -> str:
    if href.startswith("http"):
        return href
    if href.startswith("/"):
        return BASE_URL + href
    return f"{BASE_URL}/{href.lstrip('/')}"


def fetch_device_links(max_devices: int = 150) -> List[str]:
    """
    Fetch device detail URLs from the PhoneDB listing page.
    """
    session = _create_session()
    logger.info("Fetching device list from %s", DEVICE_LIST_URL)

    resp = session.get(DEVICE_LIST_URL, timeout=20)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    links: List[str] = []
    seen: set = set()

    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "index.php" in href and "m=device" in href and "id=" in href:
            # Ensure we land on the detailed specs view
            if "d=detailed_specs" not in href:
                sep = "&" if "?" in href else "?"
                href = href + sep + "d=detailed_specs"
            url = _full_url(href)
            if url not in seen:
                seen.add(url)
                links.append(url)
        if len(links) >= max_devices:
            break

    logger.info("Discovered %d device links", len(links))
    return links


def _parse_mib_gib_or_gb_to_gb(text: str) -> Optional[int]:
    """
    Convert memory strings to integer GB.
    Handles: '4096 MiB', '8 GiB', '8 GB', '256GB'

    FIX: Old version only handled MiB/GiB.  PhoneDB also uses plain 'GB'
    in some entries, so we now handle all three variants.
    """
    text = text.replace(",", " ")

    gib_match = re.search(r"(\d+(?:\.\d+)?)\s*GiB", text, re.IGNORECASE)
    if gib_match:
        return max(1, int(round(float(gib_match.group(1)))))

    gb_match = re.search(r"(\d+(?:\.\d+)?)\s*GB", text, re.IGNORECASE)
    if gb_match:
        return max(1, int(round(float(gb_match.group(1)))))

    mib_match = re.search(r"(\d+(?:\.\d+)?)\s*MiB", text, re.IGNORECASE)
    if mib_match:
        val = float(mib_match.group(1))
        return max(1, int(round(val / 1024.0)))

    return None


def _parse_battery_mah(text: str) -> Optional[int]:
    m = re.search(r"(\d+(?:\.\d+)?)\s*mAh", text, re.IGNORECASE)
    return int(round(float(m.group(1)))) if m else None


def _parse_camera_mp(text: str) -> Optional[int]:
    # Return the largest MP value found (primary sensor)
    matches = re.findall(r"(\d+(?:\.\d+)?)\s*MP", text, re.IGNORECASE)
    return max(int(round(float(v))) for v in matches) if matches else None


def _parse_price_inr(specs: Dict[str, str]) -> float:
    """
    Extract price from PhoneDB specs.

    PhoneDB stores price as a bare number under the key 'Price', e.g.:
        'Price' → '9999'

    It never includes a currency symbol in that field, so we must NOT
    require one.  We read the 'Price' key directly and parse the first
    numeric value from it.

    We still do a currency-symbol scan as a secondary fallback for any
    site that does embed INR / Rs / ₹ in a field value.
    """
    def _extract_number(text: str) -> Optional[float]:
        """Return the first numeric value (with optional commas) in text."""
        m = re.search(r'([\d,]+(?:\.\d{1,2})?)', text.strip())
        if m:
            try:
                return float(m.group(1).replace(",", ""))
            except ValueError:
                return None
        return None

    def _amount_after_currency(text: str) -> Optional[float]:
        """Match explicit markers: 'INR 14999', '₹14,999', 'Rs 14999'."""
        m = re.search(
            r'(?:INR|Rs\.?|₹)\s*([\d,]+(?:\.\d{1,2})?)',
            text,
            re.IGNORECASE,
        )
        if m:
            try:
                return float(m.group(1).replace(",", ""))
            except ValueError:
                return None
        return None

    # ── 1. Direct 'Price' key — PhoneDB stores a bare number here ────────────
    raw_price = specs.get("Price", "").strip()
    if raw_price:
        amount = _extract_number(raw_price)
        if amount is not None and amount > 0:
            return amount

    # ── 2. Any field whose *key* contains "price" or "geographical" ──────────
    for key, value in specs.items():
        key_lower = key.lower()
        if key_lower == "price":
            continue  # already handled above
        if "price" in key_lower or "geographical" in key_lower:
            amount = _amount_after_currency(value) or _extract_number(value)
            if amount is not None and amount > 0:
                return amount

    # ── 3. Fallback: any value that mentions INR / ₹ ─────────────────────────
    for value in specs.values():
        if "inr" in value.lower() or "₹" in value:
            amount = _amount_after_currency(value)
            if amount is not None and amount > 0:
                return amount

    return 0.0


def _detect_os(platform_text: str, os_text: Optional[str] = None) -> str:
    """
    Detect OS from platform/os spec fields.
    FIX: Added HarmonyOS detection and better fallback handling.
    """
    combined = " ".join(filter(None, [platform_text or "", os_text or ""])).lower()

    if "android" in combined:
        return "Android"
    if "ios" in combined or "ipad" in combined or "iphone" in combined:
        return "iOS"
    if "windows" in combined:
        return "Windows"
    if "harmonyos" in combined or "harmony" in combined:
        return "HarmonyOS"
    if "kaios" in combined:
        return "KaiOS"

    # Return first word of platform as best-effort (not 'Unknown' if we have something)
    if platform_text and platform_text.strip():
        return platform_text.split()[0]

    return "Unknown"


def _parse_specs_table(soup: BeautifulSoup) -> Dict[str, str]:
    """
    Build a flat key→value mapping from all <table> elements on the page.
    PhoneDB uses simple <tr><th>Label</th><td>Value</td></tr> rows.
    """
    specs: Dict[str, str] = {}
    for table in soup.find_all("table"):
        for row in table.find_all("tr"):
            cells = row.find_all(["th", "td"])
            if len(cells) >= 2:
                key = cells[0].get_text(" ", strip=True)
                value = cells[1].get_text(" ", strip=True)
                if key and value:
                    specs[key] = value
    return specs


def parse_device_page(html: str) -> Optional[ScrapedPhone]:
    soup = BeautifulSoup(html, "html.parser")
    specs = _parse_specs_table(soup)

    # ── Device name ───────────────────────────────────────────────────────────
    name = specs.get("Model") or specs.get("Device")
    if not name:
        h1 = soup.find("h1")
        name = h1.get_text(" ", strip=True) if h1 else None
    if not name:
        logger.warning("Could not determine model name — skipping page")
        return None

    name = normalise_phone_name(name)

    # ── OS ────────────────────────────────────────────────────────────────────
    os_name = _detect_os(
        specs.get("Platform", ""),
        specs.get("Operating System", "") or specs.get("OS", ""),
    )

    # ── Chipset ───────────────────────────────────────────────────────────────
    # PhoneDB splits chipset info across 'CPU', 'Chipset', 'SoC' keys
    chipset = (
        specs.get("SoC", "")
        or specs.get("Chipset", "")
        or specs.get("CPU", "")
    ).strip()

    # ── RAM ───────────────────────────────────────────────────────────────────
    ram_raw = (
        specs.get("RAM Capacity", "")
        or specs.get("RAM", "")
        or specs.get("Memory", "")
    )
    ram_gb = _parse_mib_gib_or_gb_to_gb(ram_raw) or 0

    # ── Storage ───────────────────────────────────────────────────────────────
    storage_raw = (
        specs.get("Non-volatile Memory Capacity", "")
        or specs.get("Internal Storage", "")
        or specs.get("Storage", "")
        or specs.get("Internal", "")
    )
    storage_gb = _parse_mib_gib_or_gb_to_gb(storage_raw) or 0

    # ── Camera ────────────────────────────────────────────────────────────────
    camera_raw = (
        specs.get("Number of effective pixels", "")
        or specs.get("Main Camera", "")
        or specs.get("Camera", "")
    )
    camera_mp = _parse_camera_mp(camera_raw) or 0

    # ── Battery ───────────────────────────────────────────────────────────────
    battery_raw = (
        specs.get("Nominal Battery Capacity", "")
        or specs.get("Battery Capacity", "")
        or specs.get("Battery", "")
    )
    battery_mah = _parse_battery_mah(battery_raw) or 0

    # ── Price ─────────────────────────────────────────────────────────────────
    price = _parse_price_inr(specs)

    logger.debug(
        "%s → battery=%d ram=%d storage=%d camera=%d os=%s price=%.0f",
        name, battery_mah, ram_gb, storage_gb, camera_mp, os_name, price,
    )

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
    Main entrypoint used by the backend and for manual runs.
    Returns the number of successfully upserted phone records.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    session = _create_session()
    links = fetch_device_links(max_devices=max_devices)
    logger.info("Starting PhoneDB scrape of up to %d devices", len(links))

    success_count = 0

    for idx, url in enumerate(links, start=1):
        try:
            logger.info("Fetching device %d/%d: %s", idx, len(links), url)
            resp = session.get(url, timeout=25)
            resp.raise_for_status()

            phone = parse_device_page(resp.text)
            if not phone:
                logger.warning("Skipping %s — parse returned None", url)
                continue

            logger.info(
                "Parsed %-40s | battery=%4d | camera=%2dMP | RAM=%2dGB | "
                "storage=%3dGB | OS=%-8s | price=%.0f",
                phone.name[:40], phone.battery, phone.camera,
                phone.ram, phone.storage, phone.os, phone.price,
            )

            for warning in validate_phone_dict(phone.to_dict()):
                logger.warning(warning)

            upsert_phone(phone.to_dict())
            success_count += 1

        except Exception as exc:
            logger.exception("Error while processing %s: %s", url, exc)
        finally:
            time.sleep(REQUEST_DELAY_SECONDS)

    logger.info("PhoneDB scraper finished — upserted %d devices.", success_count)
    return success_count


if __name__ == "__main__":
    run_scraper()