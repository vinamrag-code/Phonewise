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
from typing import Dict, List, Optional, Tuple

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
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
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
    s.headers.update({
        "User-Agent": USER_AGENT,
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    })
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
    seen: set = set()

    for list_url in BRAND_LIST_URLS:
        if len(links) >= max_devices:
            break

        logger.info("Fetching brand list from %s", list_url)
        try:
            resp = session.get(list_url, timeout=20)
            resp.raise_for_status()

            soup = BeautifulSoup(resp.text, "html.parser")

            # Device links are within .makers ul li a
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
        except Exception as e:
            logger.error("Error fetching %s: %s", list_url, e)
            continue

    logger.info("Discovered %d GSMArena device links", len(links))
    return links


def _parse_specs_table(soup: BeautifulSoup) -> Dict[str, str]:
    """
    Build a flat mapping of spec label -> value from GSMArena's specs page.

    GSMArena real HTML structure:
      <div id="specs-list">
        <table>
          <tr>
            <td class="ttl"><a>Label</a></td>
            <td class="nfo">Value</td>
          </tr>
          ...
        </table>
      </div>

    FIX: The old version searched for div.specs-list *inside* #specs-list,
    which doesn't exist. We now query all <tr> rows directly under #specs-list.
    """
    specs: Dict[str, str] = {}

    specs_list = soup.find("div", id="specs-list")
    if not specs_list:
        logger.debug("No #specs-list div found on page")
        return specs

    for row in specs_list.find_all("tr"):
        # Label is in <td class="ttl">, value is in <td class="nfo">
        ttl = row.find("td", class_="ttl")
        nfo = row.find("td", class_="nfo")
        if ttl and nfo:
            key = ttl.get_text(" ", strip=True)
            value = nfo.get_text(" ", strip=True)
            if key and value:
                specs[key] = value

    logger.debug("Parsed %d spec entries from #specs-list", len(specs))
    return specs


def _parse_battery_info(specs: Dict[str, str]) -> int:
    """
    Parse battery capacity in mAh.
    GSMArena key: 'Battery' under the Battery section.
    Example values: "Li-Ion 5000 mAh, non-removable"
    """
    for key, value in specs.items():
        if "battery" in key.lower():
            match = re.search(r'(\d[\d,]+)\s*mAh', value, re.IGNORECASE)
            if match:
                return int(match.group(1).replace(",", ""))
    return 0


def _parse_camera_info(specs: Dict[str, str]) -> int:
    """
    Parse main (rear) camera megapixels.
    GSMArena key: 'Main Camera' (newer pages) or 'Primary camera'.
    Example: "50 MP, f/1.8, 24mm (wide), 1/1.56\", 1.0µm, PDAF"
    Returns the highest MP figure found (primary sensor).
    """
    # Priority order: 'Main Camera' is the GSMArena label for the rear camera section
    priority_keys = ["Main Camera", "Single", "Dual", "Triple", "Quad", "Penta"]

    # First try the main camera field directly
    for key in list(specs.keys()):
        if key.lower() in ("main camera",):
            value = specs[key]
            mp_vals = re.findall(r'(\d+)\s*MP', value, re.IGNORECASE)
            if mp_vals:
                return max(int(v) for v in mp_vals)

    # Fallback: scan all keys that look like camera entries
    best_mp = 0
    for key, value in specs.items():
        key_lower = key.lower()
        # Avoid front/selfie cameras
        if any(skip in key_lower for skip in ("front", "selfie", "video", "features", "secondary")):
            continue
        if any(cam in key_lower for cam in ("camera", "single", "dual", "triple", "quad")):
            mp_vals = re.findall(r'(\d+)\s*MP', value, re.IGNORECASE)
            if mp_vals:
                best_mp = max(best_mp, max(int(v) for v in mp_vals))

    return best_mp


def _parse_memory_info(specs: Dict[str, str]) -> Tuple[int, int]:
    """
    Parse RAM and internal storage.
    GSMArena key: 'Internal' under the Memory section.
    Example values:
      "128GB 8GB RAM"
      "256GB 12GB RAM, 512GB 12GB RAM"
      "8 GB RAM, 256 GB"

    FIX: Old version used 'Memory' / 'Internal memory' keys that don't exist
    on GSMArena. The real key is 'Internal'.
    """
    ram = 0
    storage = 0

    # GSMArena uses 'Internal' as the key for "storage + RAM" combos
    internal = specs.get("Internal", "")
    if not internal:
        # Some older pages use 'Memory'
        internal = specs.get("Memory", "")

    if internal:
        # RAM: look for patterns like "8GB RAM" or "8 GB RAM"
        ram_match = re.search(r'(\d+)\s*GB\s+RAM', internal, re.IGNORECASE)
        if ram_match:
            ram = int(ram_match.group(1))

        # Storage: first GB number that is NOT followed by "RAM"
        storage_match = re.search(r'(\d+)\s*GB(?!\s*RAM)', internal, re.IGNORECASE)
        if storage_match:
            storage = int(storage_match.group(1))

    return ram, storage


def _parse_chipset_info(specs: Dict[str, str]) -> str:
    """
    Parse chipset/processor.
    GSMArena key: 'Chipset' under the Platform section.
    Example: "Qualcomm SM8650-AC Snapdragon 8 Gen 3 (4 nm)"

    FIX: Old version checked 'Platform' and 'CPU' which are separate rows.
    The human-readable chipset name is under 'Chipset'.
    """
    chipset = specs.get("Chipset", "").strip()
    if not chipset:
        # Fallback to CPU row
        chipset = specs.get("CPU", "").strip()
    return chipset


def _parse_os_info(specs: Dict[str, str]) -> str:
    """
    Parse operating system.
    GSMArena key: 'OS' under the Platform section.
    Example: "Android 14, upgradable to Android 15"

    FIX: Old version tried 'Operating system' and 'Platform' first,
    but GSMArena's actual label is simply 'OS'.
    """
    os_raw = specs.get("OS", "")
    if not os_raw:
        # Some pages nest this under 'Platform' → check that too
        os_raw = specs.get("Platform", "")

    if not os_raw:
        return "Unknown"

    os_lower = os_raw.lower()
    if "android" in os_lower:
        return "Android"
    if "ios" in os_lower or "iphone os" in os_lower or "ipados" in os_lower:
        return "iOS"
    if "windows" in os_lower:
        return "Windows"
    if "harmonyos" in os_lower or "harmony" in os_lower:
        return "HarmonyOS"

    # Return the first meaningful word/phrase as a best-effort value
    return os_raw.split(",")[0].strip()


def _parse_price(specs: Dict[str, str]) -> float:
    """
    Try to extract price (INR preferred) from the specs.
    GSMArena key: 'Price' under the Misc / Launch section.
    Example values:
      "About 900 EUR"
      "INR 79,999"
      "$ 999"

    FIX: Old version looked for 'Price group' / 'Launch price' which are
    not real GSMArena keys. The real key is 'Price'.
    We now prefer an INR value and fall back to any numeric price.
    """
    raw = specs.get("Price", "")
    if not raw or raw.strip().lower() in ("n/a", "unavailable", ""):
        return 0.0

    # Prefer explicit INR amount
    inr_match = re.search(
        r'(?:INR|Rs\.?|₹)\s*([\d,]+(?:\.\d{1,2})?)', raw, re.IGNORECASE
    )
    if inr_match:
        try:
            return float(inr_match.group(1).replace(",", ""))
        except ValueError:
            pass

    # Fall back to any leading price figure (e.g. "About 900 EUR" → 900)
    num_match = re.search(r'([\d,]+(?:\.\d{1,2})?)', raw)
    if num_match:
        try:
            return float(num_match.group(1).replace(",", ""))
        except ValueError:
            pass

    return 0.0


def parse_device_page(html: str, url: str) -> Optional[ScrapedPhone]:
    soup = BeautifulSoup(html, "html.parser")

    # ── Device name ──────────────────────────────────────────────────────────
    # GSMArena uses <h1 class="specs-phone-name-title"> on specs pages
    name = None
    for selector in (
        "h1.specs-phone-name-title",
        "h1[data-spec='modelname']",
        "h1",
    ):
        el = soup.select_one(selector)
        if el:
            name = el.get_text(strip=True)
            break

    if not name:
        name = url.split("/")[-1].replace(".php", "").replace("-", " ").title()
        logger.warning("Using URL-derived name for %s", url)

    # ── Specs table ───────────────────────────────────────────────────────────
    specs = _parse_specs_table(soup)
    if not specs:
        logger.warning("Empty specs table for %s — page may have changed structure", url)

    # ── Individual fields ─────────────────────────────────────────────────────
    battery_mah = _parse_battery_info(specs)
    camera_mp   = _parse_camera_info(specs)
    ram_gb, storage_gb = _parse_memory_info(specs)
    chipset     = _parse_chipset_info(specs)
    os_name     = _parse_os_info(specs)
    price       = _parse_price(specs)

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
    Main entrypoint for scraping GSMArena.
    Returns the number of successfully upserted phone records.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    session = _create_session()
    links = fetch_device_links(max_devices=max_devices)
    logger.info("Starting GSMArena scrape of up to %d devices", len(links))

    success_count = 0

    for idx, url in enumerate(links, start=1):
        try:
            logger.info("Fetching device %d/%d: %s", idx, len(links), url)
            resp = session.get(url, timeout=25)
            resp.raise_for_status()

            phone = parse_device_page(resp.text, url)
            if not phone:
                logger.warning("Skipping %s — parse returned None", url)
                continue

            logger.info(
                "Parsed %-40s | battery=%4d | camera=%2dMP | RAM=%2dGB | "
                "storage=%3dGB | OS=%-8s | price=%.0f",
                phone.name[:40], phone.battery, phone.camera,
                phone.ram, phone.storage, phone.os, phone.price,
            )

            upsert_phone(phone.to_dict())
            success_count += 1

        except Exception as exc:
            logger.exception("Error while processing %s: %s", url, exc)
        finally:
            time.sleep(REQUEST_DELAY_SECONDS)

    logger.info("GSMArena scraper finished — upserted %d devices.", success_count)
    return success_count


if __name__ == "__main__":
    run_scraper()