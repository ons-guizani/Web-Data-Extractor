import re
import pandas as pd
from rapidfuzz import fuzz

def clean_name(name: str) -> str:
    """Lowercase, remove punctuation, collapse whitespace."""
    name = str(name).lower()
    name = re.sub(r"[^a-z0-9 ]", " ", name)
    name = re.sub(r"\s+", " ", name)
    return name.strip()

def match_products(df1: pd.DataFrame, df2: pd.DataFrame, threshold: int = 75) -> pd.DataFrame:
    """
    Fuzzy-match every product in df1 (Mytek) against df2 (Tunisianet).
    Returns a DataFrame of the best matches above `threshold`.
    """
    matches = []

    for _, row1 in df1.iterrows():
        best_score = 0
        best_match = None

        for _, row2 in df2.iterrows():
            score = fuzz.token_sort_ratio(row1["clean_name"], row2["clean_name"])
            if score > best_score:
                best_score = score
                best_match = row2

        if best_match is not None and best_score >= threshold:
            matches.append({
                "name"             : row1["name"],
                "mytek_price"      : row1["price"],
                "mytek_url"        : row1["url"],
                "tunisianet_name"  : best_match["name"],
                "tunisianet_price" : best_match["price"],
                "tunisianet_url"   : best_match["url"],
                "match_score"      : best_score,
            })

    return pd.DataFrame(matches)