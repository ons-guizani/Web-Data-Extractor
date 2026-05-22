export interface ProductSpecs {
  screen: string;
  processor: string;
  ram: string;
  storage: string;
  gpu: string;
  os: string;
}

export interface MatchedProduct {
  match_score: number;
  cheapest_source: string;
  price_difference: number;
  savings_pct: number;
  mytek_name: string;
  mytek_price: number;
  mytek_price_display: string;
  mytek_url: string;
  mytek_image: string;
  mytek_brand: string;
  mytek_specs: ProductSpecs;
  tunisianet_name: string;
  tunisianet_price: number;
  tunisianet_price_display: string;
  tunisianet_url: string;
  tunisianet_image: string;
  tunisianet_description: string;
  tunisianet_discount: string;
}

export interface Stats {
  mytek_cheaper: number;
  tunisianet_cheaper: number;
  same_price: number;
  total_matched: number;
  avg_difference: number;
  max_savings: number;
}
