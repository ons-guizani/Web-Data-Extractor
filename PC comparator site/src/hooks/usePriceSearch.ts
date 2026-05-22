import { useState, useEffect, useRef, useCallback } from 'react';
import Fuse from 'fuse.js';
import type { IFuseOptions } from 'fuse.js';
import type { MatchedProduct, Stats } from '@/types';

export interface SearchState {
  matches: MatchedProduct[];
  stats: Stats | null;
  loading: boolean;
  error: string | null;
  fuseReady: boolean;
}

const FUSE_OPTIONS: IFuseOptions<MatchedProduct> = {
  keys: [
    { name: 'mytek_name', weight: 0.45 },
    { name: 'tunisianet_name', weight: 0.35 },
    { name: 'mytek_brand', weight: 0.2 }
  ],
  threshold: 0.4,
  includeScore: true,
  minMatchCharLength: 2,
  ignoreLocation: true,
  shouldSort: true
};

export function usePriceSearch() {
  const [state, setState] = useState<SearchState>({
    matches: [],
    stats: null,
    loading: true,
    error: null,
    fuseReady: false
  });
  
  const fuseRef = useRef<Fuse<MatchedProduct> | null>(null);
  const allMatchesRef = useRef<MatchedProduct[]>([]);

  // Load data on mount
  useEffect(() => {
    let cancelled = false;

    async function loadData() {
      try {
        const [matchesRes, statsRes] = await Promise.all([
          fetch('/data/matches.json'),
          fetch('/data/stats.json')
        ]);

        if (!matchesRes.ok || !statsRes.ok) {
          throw new Error('Failed to load price data');
        }

        const [matches, stats] = await Promise.all([
          matchesRes.json() as Promise<MatchedProduct[]>,
          statsRes.json() as Promise<Stats>
        ]);

        if (cancelled) return;

        // Initialize Fuse
        fuseRef.current = new Fuse(matches, FUSE_OPTIONS);
        allMatchesRef.current = matches;

        setState({
          matches: [],
          stats,
          loading: false,
          error: null,
          fuseReady: true
        });
      } catch (err) {
        if (!cancelled) {
          setState(prev => ({
            ...prev,
            loading: false,
            error: err instanceof Error ? err.message : 'Unknown error'
          }));
        }
      }
    }

    loadData();
    return () => { cancelled = true; };
  }, []);

  // Search function
  const search = useCallback((query: string): MatchedProduct[] => {
    if (!fuseRef.current || !query.trim()) {
      return [];
    }
    
    const results = fuseRef.current.search(query.trim());
    return results.slice(0, 20).map(r => r.item);
  }, []);

  // Get top savings
  const getTopSavings = useCallback((limit: number = 10): MatchedProduct[] => {
    return [...allMatchesRef.current]
      .sort((a, b) => b.price_difference - a.price_difference)
      .slice(0, limit);
  }, []);

  // Get all matches for a brand
  const getByBrand = useCallback((brand: string): MatchedProduct[] => {
    return allMatchesRef.current.filter(m => 
      m.mytek_brand.toLowerCase() === brand.toLowerCase()
    );
  }, []);

  return {
    ...state,
    search,
    getTopSavings,
    getByBrand
  };
}
