"""
Mytek PC Portable Scraper
==========================
Scrapes all laptop listings from https://www.mytek.tn/informatique/ordinateurs-portables/pc-portable.html
navigating through all pages (currently 10 pages / ~448 products).

Key insight: Mytek embeds ALL product data as data-* attributes on divs inside #seo-product-data
before JavaScript renders the visible cards. This means we can parse the raw HTML without
waiting for dynamic rendering — the scraper uses Selenium to handle any JS-gating but
extracts from the hidden SEO data block which is always present.

Requirements:
    pip install selenium beautifulsoup4 pandas openpyxl webdriver-manager

Usage:
    python mytek_scraper.py

Output:
    mytek_laptops.csv   — all products in CSV format
    mytek_laptops.xlsx  — same data as Excel workbook
"""

import time
import csv
import re
import logging
from pathlib import Path

# ── Third-party ──────────────────────────────────────────────────────────────
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd

# ── Configuration ─────────────────────────────────────────────────────────────
BASE_URL    = "https://www.mytek.tn/informatique/ordinateurs-portables/pc-portable.html"
CATEGORY_ID = "38"
OUTPUT_CSV  = "mytek_laptops.csv"
OUTPUT_XLSX = "mytek_laptops.xlsx"
IMAGE_BASE  = "https://mk-media.mytek.tn/media/catalog/product"
PAGE_DELAY  = 2.5        # seconds between pages (be polite)
MAX_RETRIES = 3
HEADLESS    = True

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


# ── Browser setup ─────────────────────────────────────────────────────────────
def build_driver() -> webdriver.Chrome:
    opts = Options()
    if HEADLESS:
        opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument("--window-size=1400,900")
    opts.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)
    service = Service(ChromeDriverManager().install())
    driver  = webdriver.Chrome(service=service, options=opts)
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {"source": "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})"},
    )
    return driver


# ── Wait helpers ──────────────────────────────────────────────────────────────
def wait_for_seo_data(driver: webdriver.Chrome, timeout: int = 20) -> bool:
    """Wait until the hidden #seo-product-data block contains at least one product."""
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#seo-product-data > div[data-id]"))
        )
        return True
    except TimeoutException:
        return False


def wait_for_total_count(driver: webdriver.Chrome, timeout: int = 15) -> int:
    """Extract total product count from the page."""
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#total-count-data"))
        )
        el = driver.find_element(By.CSS_SELECTOR, "#total-count-data")
        return int(el.get_attribute("data-count") or 0)
    except Exception:
        return 0


# ── Pagination ────────────────────────────────────────────────────────────────
def get_total_pages(driver: webdriver.Chrome) -> int:
    """Read the last page number from the pagination widget."""
    try:
        links = driver.find_elements(By.CSS_SELECTOR, ".custom-pagination .page-link")
        nums = []
        for a in links:
            txt = a.text.strip()
            if txt.isdigit():
                nums.append(int(txt))
        return max(nums) if nums else 1
    except Exception:
        return 1


# ── Product extraction ────────────────────────────────────────────────────────
def parse_products_from_page(page_source: str) -> list[dict]:
    """
    Extract all product data from the hidden #seo-product-data block.
    Mytek embeds complete product info as data-* attributes:
      data-id, data-name, data-url, data-sku, data-price, data-final-price,
      data-image, data-erpstock (availability), data-manufacturer, data-description
    """
    soup    = BeautifulSoup(page_source, "html.parser")
    block   = soup.select_one("#seo-product-data")
    if not block:
        return []

    products = []
    for div in block.select("div[data-id]"):
        raw_price       = div.get("data-price", "").strip()
        raw_final_price = div.get("data-final-price", "").strip()
        image_path      = div.get("data-image", "").strip()

        # Build full image URL
        if image_path and not image_path.startswith("http"):
            image_url = IMAGE_BASE + image_path
        else:
            image_url = image_path

        # Parse numeric prices
        try:
            price_num = float(raw_price) if raw_price else None
        except ValueError:
            price_num = None
        try:
            final_price_num = float(raw_final_price) if raw_final_price else None
        except ValueError:
            final_price_num = None

        # Discount calculation
        if price_num and final_price_num and final_price_num < price_num:
            discount_pct = round((1 - final_price_num / price_num) * 100, 1)
            is_on_sale   = True
        else:
            discount_pct = 0.0
            is_on_sale   = False

        description = div.get("data-description", "").strip()

        # Parse structured specs from description (colon-separated bullet format)
        specs = _parse_description_specs(description)

        product = {
            "product_id"       : div.get("data-id", "").strip(),
            "name"             : div.get("data-name", "").strip(),
            "url"              : div.get("data-url", "").strip(),
            "sku"              : div.get("data-sku", "").strip(),
            "brand"            : div.get("data-manufacturer", "").strip(),
            "price_tnd"        : raw_price,
            "final_price_tnd"  : raw_final_price,
            "price_numeric"    : price_num,
            "final_price_numeric": final_price_num,
            "is_on_sale"       : is_on_sale,
            "discount_pct"     : discount_pct if is_on_sale else "",
            "availability"     : div.get("data-erpstock", "").strip(),
            "image_url"        : image_url,
            "description"      : description,
            # Parsed specs
            "screen"           : specs.get("ecran", ""),
            "processor"        : specs.get("processeur", ""),
            "os"               : specs.get("systeme", ""),
            "ram"              : specs.get("memoire", ""),
            "storage"          : specs.get("disque", ""),
            "gpu"              : specs.get("graphique", ""),
        }
        products.append(product)

    return products


def _parse_description_specs(desc: str) -> dict:
    """
    Parse key specs from the Mytek description string.
    Format: "Écran ... - Processeur: ... - Système d'exploitation: ... - Mémoire RAM: ... - Disque Dur: ... - Carte Graphique: ..."
    """
    specs = {}
    if not desc:
        return specs

    # Split on ' - ' segments
    segments = re.split(r'\s+-\s+', desc)
    for seg in segments:
        low = seg.lower()
        if "écran" in low or "ecran" in low:
            specs["ecran"] = seg.strip()
        elif "processeur" in low:
            # Extract value after colon
            m = re.search(r'processeur\s*:\s*(.+)', seg, re.IGNORECASE)
            specs["processeur"] = m.group(1).strip() if m else seg.strip()
        elif "système" in low or "systeme" in low or "exploitation" in low:
            m = re.search(r'exploitation\s*:\s*(.+)', seg, re.IGNORECASE)
            specs["systeme"] = m.group(1).strip() if m else seg.strip()
        elif "mémoire" in low or "memoire" in low:
            m = re.search(r'(?:mémoire|memoire)(?:\s+ram)?\s*:\s*(.+)', seg, re.IGNORECASE)
            specs["memoire"] = m.group(1).strip() if m else seg.strip()
        elif "disque" in low:
            m = re.search(r'disque(?:\s+dur)?\s*:\s*(.+)', seg, re.IGNORECASE)
            specs["disque"] = m.group(1).strip() if m else seg.strip()
        elif "graphique" in low or "carte" in low:
            m = re.search(r'graphique\s*:\s*(.+)', seg, re.IGNORECASE)
            specs["graphique"] = m.group(1).strip() if m else seg.strip()

    return specs


# ── Page scraper ──────────────────────────────────────────────────────────────
def scrape_page(driver: webdriver.Chrome, page: int) -> list[dict]:
    """Navigate to the given page and extract all products."""
    if page == 1:
        url = f"{BASE_URL}?categoryId={CATEGORY_ID}"
    else:
        url = f"{BASE_URL}?categoryId={CATEGORY_ID}&p={page}"

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            driver.get(url)
            if not wait_for_seo_data(driver):
                raise TimeoutException(f"No seo-product-data found on page {page}")
            # Small extra wait to ensure all divs are rendered
            time.sleep(1.0)
            break
        except TimeoutException as exc:
            log.warning("Page %d attempt %d/%d: %s", page, attempt, MAX_RETRIES, exc)
            if attempt == MAX_RETRIES:
                log.error("Giving up on page %d", page)
                return []
            time.sleep(3)

    products = parse_products_from_page(driver.page_source)
    log.info("Page %3d → %d products", page, len(products))
    return products


# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    log.info("Starting Mytek PC Portable scraper …")
    driver = build_driver()

    try:
        # ── Load page 1 and discover pagination ──────────────────────────────
        url_p1 = f"{BASE_URL}?categoryId={CATEGORY_ID}"
        driver.get(url_p1)
        wait_for_seo_data(driver)

        total_pages    = get_total_pages(driver)
        total_products = wait_for_total_count(driver)
        log.info("Discovered %d products across %d pages", total_products, total_pages)

        all_products: list[dict] = []

        for page in range(1, total_pages + 1):
            products = scrape_page(driver, page)
            all_products.extend(products)
            time.sleep(PAGE_DELAY)

        log.info("Scraping complete — collected %d products", len(all_products))

        if not all_products:
            log.warning("No products collected. Exiting.")
            return

        # ── Save CSV ─────────────────────────────────────────────────────────
        fieldnames = list(all_products[0].keys())
        with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_products)
        log.info("Saved CSV  → %s", OUTPUT_CSV)

        # ── Save Excel ───────────────────────────────────────────────────────
        df = pd.DataFrame(all_products)
        with pd.ExcelWriter(OUTPUT_XLSX, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Laptops")
            ws = writer.sheets["Laptops"]
            for col in ws.columns:
                max_len = max(len(str(cell.value or "")) for cell in col)
                ws.column_dimensions[col[0].column_letter].width = min(max_len + 2, 60)
        log.info("Saved XLSX → %s", OUTPUT_XLSX)

        # ── Summary ──────────────────────────────────────────────────────────
        prices = df["final_price_numeric"].dropna()
        on_sale = df[df["is_on_sale"] == True]
        brands  = df["brand"].value_counts()

        print("\n" + "=" * 55)
        print(f"  Total products collected : {len(df)}")
        print(f"  Unique product IDs       : {df['product_id'].nunique()}")
        if not prices.empty:
            print(f"  Price range (TND)        : {prices.min():.3f} – {prices.max():.3f}")
            print(f"  Average price (TND)      : {prices.mean():.3f}")
        print(f"  Products on sale          : {len(on_sale)}")
        print(f"  Brands ({len(brands)} total):")
        for brand, count in brands.items():
            print(f"    {brand:<20} {count} products")
        print(f"\n  Availability breakdown:")
        for avail, count in df["availability"].value_counts().items():
            print(f"    {avail:<30} {count}")
        print("=" * 55)

    finally:
        driver.quit()
        log.info("Browser closed.")


if __name__ == "__main__":
    main()
