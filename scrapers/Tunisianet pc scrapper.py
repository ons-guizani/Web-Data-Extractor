"""
Tunisianet PC Portable Scraper
================================
Scrapes all laptop listings from https://www.tunisianet.com.tn/301-pc-portable-tunisie
navigating through all pages (currently 35 pages / ~819 products).

Requirements:
    pip install selenium beautifulsoup4 pandas openpyxl webdriver-manager

Usage:
    python tunisianet_scraper.py

Output:
    tunisianet_laptops.csv   — all products in CSV format
    tunisianet_laptops.xlsx  — same data as Excel workbook
"""

import time
import json
import csv
import re
import logging
from pathlib import Path
from datetime import datetime

# ── Third-party ──────────────────────────────────────────────────────────────
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd

# ── Configuration ─────────────────────────────────────────────────────────────
BASE_URL    = "https://www.tunisianet.com.tn/301-pc-portable-tunisie"
OUTPUT_CSV  = "tunisianet_laptops.csv"
OUTPUT_XLSX = "tunisianet_laptops.xlsx"
PAGE_DELAY  = 2.0        # seconds between page requests (be polite)
SCROLL_PAUSE = 0.8       # seconds after scroll (allows lazy images to load)
MAX_RETRIES = 3          # retry a page this many times on failure
HEADLESS    = True       # set False to watch the browser

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


# ── Page helpers ──────────────────────────────────────────────────────────────
def scroll_to_bottom(driver: webdriver.Chrome) -> None:
    """Scroll incrementally so lazy-loaded images / elements appear."""
    last_h = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollBy(0, 600)")
        time.sleep(SCROLL_PAUSE)
        new_h = driver.execute_script("return document.body.scrollHeight")
        if new_h == last_h:
            break
        last_h = new_h


def wait_for_products(driver: webdriver.Chrome, timeout: int = 15) -> bool:
    """Wait until at least one product card is present in the DOM."""
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "article.js-product-miniature"))
        )
        return True
    except TimeoutException:
        return False


def get_total_pages(driver: webdriver.Chrome) -> int:
    """Parse the last page number from the pagination widget."""
    try:
        page_items = driver.find_elements(By.CSS_SELECTOR, "ul.page-list li a")
        nums = []
        for a in page_items:
            txt = a.text.strip()
            if txt.isdigit():
                nums.append(int(txt))
        return max(nums) if nums else 1
    except Exception:
        return 1


def get_total_products(driver: webdriver.Chrome) -> int:
    """Parse the total product count shown in the pagination bar."""
    try:
        text = driver.find_element(By.CSS_SELECTOR, ".total-products p").text
        match = re.search(r"(\d+)", text)
        return int(match.group(1)) if match else 0
    except Exception:
        return 0


# ── Product extraction ────────────────────────────────────────────────────────
def clean_price(raw: str) -> str:
    """Return price as a plain string, e.g. '1099.000 TND'."""
    return re.sub(r"\s+", " ", raw.replace("\xa0", " ")).strip()


def parse_product(article: BeautifulSoup) -> dict:
    """Extract every available field from a single product <article>."""
    data: dict = {}

    # ── IDs ───────────────────────────────────────────────────────────────────
    data["product_id"]        = article.get("data-id-product", "")
    data["product_attr_id"]   = article.get("data-id-product-attribute", "")

    # ── Reference / SKU ───────────────────────────────────────────────────────
    ref_el = article.select_one(".product-reference")
    data["reference"] = ref_el.text.strip().strip("[]") if ref_el else ""

    # ── Name & URL ────────────────────────────────────────────────────────────
    title_el = article.select_one(".product-title a")
    if title_el:
        data["name"] = title_el.text.strip()
        data["url"]  = title_el.get("href", "").strip()
    else:
        data["name"] = ""
        data["url"]  = ""

    # ── Prices ────────────────────────────────────────────────────────────────
    price_el      = article.select_one(".price")
    old_price_el  = article.select_one(".regular-price")
    discount_el   = article.select_one(".discount-percentage, .discount-amount")

    data["price"]         = clean_price(price_el.text)      if price_el      else ""
    data["old_price"]     = clean_price(old_price_el.text)  if old_price_el  else ""
    data["discount"]      = discount_el.text.strip()         if discount_el   else ""

    # ── Description snippet ───────────────────────────────────────────────────
    desc_el = article.select_one("[id^='product-description-short-'] a")
    if not desc_el:
        desc_el = article.select_one("[id^='product-description-short-']")
    data["description_short"] = desc_el.get_text(" ", strip=True) if desc_el else ""

    # ── Image ─────────────────────────────────────────────────────────────────
    img_el = article.select_one("img[itemprop='image']")
    if not img_el:
        img_el = article.select_one("a.product-thumbnail img")
    if img_el:
        data["image_url"]      = img_el.get("src", "").strip()
        data["image_full_url"] = img_el.get("data-full-size-image-url", "").strip()
        data["image_alt"]      = img_el.get("alt", "").strip()
    else:
        data["image_url"] = data["image_full_url"] = data["image_alt"] = ""

    # ── Flags / badges (Nouveau, Promo, etc.) ─────────────────────────────────
    flags = article.select(".product-flag")
    data["flags"] = " | ".join(f.text.strip() for f in flags if f.text.strip())

    # ── Availability ──────────────────────────────────────────────────────────
    avail_el = article.select_one(".product-availability")
    data["availability"] = avail_el.text.strip() if avail_el else ""

    # ── Rating / reviews ──────────────────────────────────────────────────────
    rating_el = article.select_one(".star-content")
    data["rating"] = rating_el.get("aria-label", rating_el.text.strip()) if rating_el else ""

    review_el = article.select_one(".comments_nb")
    data["reviews_count"] = review_el.text.strip() if review_el else ""

    # ── Hidden form fields (stock quantity hint) ───────────────────────────────
    qty_el = article.find("input", id=re.compile(r"^hit_qte"))
    data["stock_qty_hint"] = qty_el.get("value", "") if qty_el else ""

    return data


# ── Page scraper ──────────────────────────────────────────────────────────────
def scrape_page(driver: webdriver.Chrome, page: int) -> list[dict]:
    """Navigate to the given page and return a list of product dicts."""
    url = BASE_URL if page == 1 else f"{BASE_URL}?page={page}"

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            driver.get(url)
            if not wait_for_products(driver):
                raise TimeoutException(f"No products found on page {page}")
            scroll_to_bottom(driver)
            break
        except TimeoutException as exc:
            log.warning("Page %d attempt %d/%d failed: %s", page, attempt, MAX_RETRIES, exc)
            if attempt == MAX_RETRIES:
                log.error("Giving up on page %d", page)
                return []
            time.sleep(3)

    soup     = BeautifulSoup(driver.page_source, "html.parser")
    articles = soup.select("article.js-product-miniature")
    products = [parse_product(a) for a in articles]

    log.info("Page %3d → %d products", page, len(products))
    return products


# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    log.info("Starting Tunisianet PC Portable scraper …")
    driver = build_driver()

    try:
        # ── Load page 1 and discover pagination ──────────────────────────────
        driver.get(BASE_URL)
        wait_for_products(driver)
        total_pages    = get_total_pages(driver)
        total_products = get_total_products(driver)
        log.info("Found %d products across %d pages", total_products, total_pages)

        all_products: list[dict] = []

        for page in range(1, total_pages + 1):
            products = scrape_page(driver, page)
            all_products.extend(products)
            time.sleep(PAGE_DELAY)

        log.info("Scraping complete. Total collected: %d products", len(all_products))

        # ── Save CSV ─────────────────────────────────────────────────────────
        if all_products:
            fieldnames = list(all_products[0].keys())
            with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(all_products)
            log.info("Saved CSV  → %s", OUTPUT_CSV)

            # ── Save Excel ───────────────────────────────────────────────────
            df = pd.DataFrame(all_products)

            # Clean up price columns for numeric analysis
            for col in ["price", "old_price"]:
                df[col + "_numeric"] = (
                    df[col]
                    .str.replace(r"[^\d,\.]", "", regex=True)
                    .str.replace(",", ".")
                    .replace("", None)
                    .astype(float, errors="ignore")
                )

            with pd.ExcelWriter(OUTPUT_XLSX, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, sheet_name="Laptops")
                # Auto-fit columns
                ws = writer.sheets["Laptops"]
                for col in ws.columns:
                    max_len = max(len(str(cell.value or "")) for cell in col)
                    ws.column_dimensions[col[0].column_letter].width = min(max_len + 2, 60)

            log.info("Saved XLSX → %s", OUTPUT_XLSX)

            # ── Quick summary ────────────────────────────────────────────────
            print("\n" + "=" * 50)
            print(f"  Total products scraped : {len(df)}")
            print(f"  Unique product IDs     : {df['product_id'].nunique()}")
            if "price_numeric" in df.columns:
                prices = df["price_numeric"].dropna()
                if not prices.empty:
                    print(f"  Price range (TND)      : {prices.min():.3f} – {prices.max():.3f}")
                    print(f"  Average price (TND)    : {prices.mean():.3f}")
            discounted = df[df["discount"] != ""]
            print(f"  Products on discount   : {len(discounted)}")
            print("=" * 50)

        else:
            log.warning("No products were collected!")

    finally:
        driver.quit()
        log.info("Browser closed.")


if __name__ == "__main__":
    main()