import pandas as pd

def compare_prices(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds three columns to the matched DataFrame:
      - cheapest_source  : "Mytek" | "Tunisianet" | "Same"
      - price_difference : absolute difference in TND
      - savings_%        : percentage saved vs the more expensive option
    """
    cheapest = []
    diff     = []
    savings  = []

    for _, row in df.iterrows():
        p1 = float(row["mytek_price"])
        p2 = float(row["tunisianet_price"])

        if p1 < p2:
            cheapest.append("Mytek")
        elif p2 < p1:
            cheapest.append("Tunisianet")
        else:
            cheapest.append("Same")

        difference = abs(p1 - p2)
        diff.append(round(difference, 3))

        pct = (difference / max(p1, p2)) * 100 if max(p1, p2) > 0 else 0
        savings.append(round(pct, 2))

    df = df.copy()
    df["cheapest_source"]  = cheapest
    df["price_difference"] = diff
    df["savings_%"]        = savings

    return df