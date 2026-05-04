import os
import pandas as pd
from matcher import clean_name, match_products
from compare import compare_prices
from report import generate_excel

def run_pipeline():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    # ── Load CSVs ──────────────────────────────────────────────
    mytek      = pd.read_csv(os.path.join(BASE_DIR, "data", "mytek.csv"))
    tunisianet = pd.read_csv(os.path.join(BASE_DIR, "data", "tunisianet.csv"))

    # ── Normalise column names ─────────────────────────────────
    mytek.columns      = mytek.columns.str.lower().str.strip()
    tunisianet.columns = tunisianet.columns.str.lower().str.strip()

    # ── Fix Mytek price column (stored as "price_numeric") ─────
    mytek = mytek.rename(columns={"price_numeric": "price"})

    # ── Fix Tunisianet price (stored as '1 099,000 DT') ────────
    tunisianet["price"] = (
        tunisianet["price"]
        .astype(str)
        .str.replace(r"[^\d,]", "", regex=True)   # keep digits and comma
        .str.replace(",", ".")                     # French decimal → dot
        .str.split(".")                            # handle "1099.000"
        .str[0]                                    # take integer part
        .astype(float)
    )

    # ── Validate required columns ──────────────────────────────
    required = ["name", "price", "url"]
    for col in required:
        if col not in mytek.columns:
            raise ValueError(f"mytek is missing column: '{col}' — found: {mytek.columns.tolist()}")
        if col not in tunisianet.columns:
            raise ValueError(f"tunisianet is missing column: '{col}' — found: {tunisianet.columns.tolist()}")

    # ── Build clean names for fuzzy matching ──────────────────
    mytek["clean_name"]      = mytek["name"].apply(clean_name)
    tunisianet["clean_name"] = tunisianet["name"].apply(clean_name)

    # ── Run pipeline ──────────────────────────────────────────
    matched  = match_products(mytek, tunisianet)
    final_df = compare_prices(matched)
    generate_excel(final_df)

    print("✅ Report Generated Successfully!")
    print(f"   Matched products : {len(final_df)}")
    print(f"   Output file      : price_report.xlsx")

if __name__ == "__main__":
    run_pipeline()