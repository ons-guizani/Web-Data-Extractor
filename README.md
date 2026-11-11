# Price Intelligence Engine: Mytek × Tunisianet

Automated market intelligence and web scraping system that collects laptop prices from Mytek and Tunisianet, matches equivalent products across both sites, and generates an Excel report with the cheapest vendor and the potential savings.

**Tunis Business School: Web Scraping & Cybersecurity Project**

## Problem

- **Tab chaos:** consumers compare prices by switching between sites manually.
- **Naming inconsistencies:** the same laptop is named differently on each platform.
- **False price assumptions:** hidden price differences between platforms cost buyers money.
- **Fragmented data:** product data is inconsistent, duplicated and unstandardized.

## Solution

1. **Automated data collection:** scrapes product names, prices, stock, URLs and specifications.
2. **Intelligent product matching:** a fuzzy matching engine identifies equivalent products despite different names.
3. **Price intelligence analysis:** compares prices, calculates savings and identifies the cheapest option.
4. **Excel reporting:** generates a formatted report with matched products, best prices and savings.

## Pipeline

| Stage | Description |
|---|---|
| 1. Browser cloaking | Chrome automated with Playwright, with stealth modifications |
| 2. Rate-limited navigation | 2.5-second delays between requests and gradual page scrolling |
| 3. Dynamic synchronization | Waits for hidden data containers to load before extraction |
| 4. Hidden SEO extraction | Extracts product data from `#seo-product-data` containers |
| 5. Data sanitization | Cleaning, normalization and alignment of extracted data |
| 6. Currency normalization | `"2 599,000 DT"` → `2599.000` |
| 7. Regex optimization | Standardizes titles: lowercase, removes punctuation, collapses whitespace |
| 8. Fuzzy cross-matching | RapidFuzz token sorting and Levenshtein similarity (85%+ match threshold) |
| 9. Price audit | Calculates savings, identifies the cheapest vendor, detects price gaps (with zero-division protection) |
| 10. Excel report | Automated, formatted price comparison with savings highlights |

## Fuzzy Matching

Identical products are named differently across the two platforms. The engine normalizes titles and sorts tokens so that word order doesn't matter: `"RTX3050 Ryzen7 Lenovo"` matches `"Lenovo Ryzen7 RTX3050"`. Each pair gets a similarity score (for example 87.9%), and pairs above the threshold are treated as the same product.

## Results

- **500+ products** analyzed with **85%+ matching accuracy**
- **Maximum savings detected:** 660 TND (22.11%) on the MSI Thin 15 Gamer Laptop (Mytek 2325 TND vs Tunisianet 2985 TND)
- **No universal cheapest platform:**
  - Mytek is cheaper by 574 TND on the Dell Pro 16 Ryzen 5
  - Tunisianet is cheaper by 450 TND on the Dell Vostro i5

## Cybersecurity Perspective

- **Passive data exposure:** both sites expose product IDs, SKUs, exact prices, stock availability, categories and image paths in hidden SEO blocks (`#seo-product-data`) in the frontend source code. This is information leakage without any server compromise or authentication bypass.
- **Security lesson:** organizations should audit what business data their frontend code exposes.
- **WAF resilience observed:** anti-bot systems, request monitoring, rate limiting and browser fingerprinting.

## Technology Stack

| Tool | Purpose |
|---|---|
| Python | Core language |
| BeautifulSoup4 | HTML parsing |
| Playwright / Selenium | Browser automation and dynamic page interaction |
| RapidFuzz | Fuzzy product matching |
| Pandas & openpyxl | Data analysis and Excel report generation |
| Regex & APScheduler | Title normalization and scheduled execution |

## Challenges & Solutions

| Challenge | Solution |
|---|---|
| Dynamic JavaScript loading | Dynamic waits instead of static timers |
| Anti-bot protection | Rate limiting, human-like browsing, fingerprint masking |
| Regional currency formats | Custom normalization to standard decimals |
| Inconsistent product names | Regex normalization plus RapidFuzz matching |

## Getting Started

```bash
# Clone the repository
git clone <your-repo-url>
cd <repo-folder>

# Install dependencies
pip install beautifulsoup4 playwright selenium rapidfuzz pandas openpyxl apscheduler
playwright install chromium

# Run the pipeline
python main.py
```

## Repository Structure

```
├── README.md
├── src/             # Scraping and matching scripts
├── data/            # Scraped data
├── reports/         # Generated Excel reports
└── presentation/    # Project presentation
```

## Ethical Use Statement

This project accesses **public data only**, with no authentication bypass. It was developed for **educational and research purposes**. Check each website's terms of service and robots.txt before scraping, and don't use this tool for commercial or abusive purposes.

## Team

- Ons Guizani
- Molka Ouelhezi
- Nour Gaja
- Isra Ben Amor
- Sirine Sboui

Tunis Business School
