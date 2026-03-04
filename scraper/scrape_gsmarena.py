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
    s.headers.update({"User-Agent": USER_AGENT})
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
        try:
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
        except Exception as e:
            logger.error(f"Error fetching {list_url}: {e}")
            continue

    logger.info("Discovered %d GSMArena device links", len(links))
    return links


def _parse_specs_table(html: str) -> Dict[str, str]:
    """
    Build a mapping from spec row label -> value from GSMArena's specs table.
    """
    soup = BeautifulSoup(html, "html.parser")
    specs: Dict[str, str] = {}

    # Find the specs list container
    specs_container = soup.find("div", id="specs-list")
    if not specs_container:
        return specs

    # Each category is in a div
    for spec_div in specs_container.find_all("div", class_="specs-list"):
        # Find all tables in this spec section
        tables = spec_div.find_all("table")
        for table in tables:
            for row in table.find_all("tr"):
                th = row.find("th", class_="ttl")
                td = row.find("td", class_="nfo")
                if th and td:
                    key = th.get_text(strip=True)
                    value = td.get_text(" ", strip=True)
                    if key and value:
                        specs[key] = value

    return specs


def _parse_battery_info(specs: Dict[str, str]) -> int:
    """
    Parse battery capacity in mAh.
    """
    # Look for battery related keys
    battery_keys = ["Battery", "Battery charging", "Battery type"]
    
    for key in battery_keys:
        if key in specs:
            value = specs[key]
            # Look for pattern like "5000 mAh" or "Li-Po 5000 mAh"
            match = re.search(r'(\d+)\s*(?:mAh|mah|MAH)', value, re.IGNORECASE)
            if match:
                return int(match.group(1))
    
    return 0


def _parse_camera_info(specs: Dict[str, str]) -> int:
    """
    Parse main camera megapixels.
    """
    # Look for camera related keys
    camera_keys = ["Main Camera", "Camera", "Primary camera", "Dual camera", "Triple camera", "Quad camera"]
    
    for key in camera_keys:
        if key in specs:
            value = specs[key]
            # Look for pattern like "50 MP" or "50MP"
            matches = re.findall(r'(\d+)\s*(?:MP|mp|Mp)', value)
            if matches:
                # Return the highest MP count (main camera)
                return max(int(mp) for mp in matches)
    
    return 0


def _parse_memory_info(specs: Dict[str, str]) -> tuple[int, int]:
    """
    Parse RAM and storage from memory specs.
    """
    memory_keys = ["Memory", "Internal", "Internal memory", "Storage"]
    ram = 0
    storage = 0
    
    for key in memory_keys:
        if key in specs:
            value = specs[key]
            
            # Parse RAM
            ram_match = re.search(r'(\d+)\s*GB\s*(?:RAM|ram)', value, re.IGNORECASE)
            if ram_match:
                ram = int(ram_match.group(1))
            
            # Parse Storage (look for GB numbers not followed by RAM)
            storage_matches = re.findall(r'(\d+)\s*GB(?!\s*RAM)', value, re.IGNORECASE)
            if storage_matches:
                storage = int(storage_matches[0])
            
            break
    
    return ram, storage


def _parse_chipset_info(specs: Dict[str, str]) -> str:
    """
    Parse chipset/processor information.
    """
    chipset_keys = ["Chipset", "Platform", "Processor", "CPU"]
    
    for key in chipset_keys:
        if key in specs:
            return specs[key].strip()
    
    return ""


def _parse_os_info(specs: Dict[str, str]) -> str:
    """
    Parse operating system information.
    """
    os_keys = ["OS", "Operating system", "Platform"]
    
    for key in os_keys:
        if key in specs:
            os_text = specs[key].lower()
            if "android" in os_text:
                return "Android"
            elif "ios" in os_text or "ipados" in os_text:
                return "iOS"
            elif "windows" in os_text:
                return "Windows"
            else:
                return specs[key].strip()
    
    return "Unknown"


def _parse_price(specs: Dict[str, str]) -> float:
    """
    Try to extract price from specs.
    """
    # Look for price related keys
    price_keys = ["Price", "Price group", "Launch price"]
    
    for key in price_keys:
        if key in specs:
            value = specs[key]
            # Look for numbers that could be prices (with optional commas and decimal points)
            match = re.search(r'(?:INR|Rs\.?|₹)?\s*([\d,]+(?:\.\d{2})?)', value, re.IGNORECASE)
            if match:
                price_str = match.group(1).replace(',', '')
                try:
                    return float(price_str)
                except ValueError:
                    continue
    
    return 0.0


def parse_device_page(html: str, url: str) -> ScrapedPhone | None:
    soup = BeautifulSoup(html, "html.parser")

    # Name - try multiple selectors
    name = None
    name_selectors = [
        "h1.specs-phone-name-title",
        "h1[data-spec='modelname']",
        ".article-info-name",
        "h1"
    ]
    
    for selector in name_selectors:
        name_elt = soup.select_one(selector)
        if name_elt:
            name = name_elt.get_text(strip=True)
            break
    
    if not name:
        # Try to get from URL as fallback
        name = url.split('/')[-1].replace('.php', '').replace('-', ' ').title()
        logger.warning(f"Using URL-derived name: {name}")

    specs = _parse_specs_table(html)
    
    # Log found specs for debugging
    logger.debug(f"Found {len(specs)} spec items for {name}")
    for key, value in list(specs.items())[:5]:  # Log first 5 specs
        logger.debug(f"  {key}: {value}")

    # Parse each component
    battery_mah = _parse_battery_info(specs)
    camera_mp = _parse_camera_info(specs)
    ram_gb, storage_gb = _parse_memory_info(specs)
    chipset = _parse_chipset_info(specs)
    os_name = _parse_os_info(specs)
    price = _parse_price(specs)

    # If price is 0 and it's a new unreleased phone, set a placeholder
    if price == 0 and "Expected" in str(specs.get("Price", "")):
        price = 1.0  # Placeholder for upcoming phones

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

            phone = parse_device_page(resp.text, url)
            if not phone:
                logger.warning("Skipping device %s due to parse failure", url)
                continue

            # Log the parsed data for debugging
            logger.info(f"Parsed {phone.name}: Battery={phone.battery}mAh, Camera={phone.camera}MP, "
                       f"RAM={phone.ram}GB, Storage={phone.storage}GB, Chipset={phone.chipset[:30]}..., "
                       f"OS={phone.os}, Price={phone.price}")

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