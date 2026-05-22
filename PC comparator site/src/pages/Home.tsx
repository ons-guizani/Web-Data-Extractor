import { useState, useMemo } from 'react';
import { usePriceSearch } from '@/hooks/usePriceSearch';
import type { MatchedProduct } from '@/types';
import {
  Search,
  TrendingDown,
  ShoppingCart,
  ExternalLink,
  Zap,
  BarChart3,
  Package,
  ArrowRight,
  ChevronDown,
  Monitor
} from 'lucide-react';

function StatCard({ icon: Icon, label, value, color }: {
  icon: React.ElementType;
  label: string;
  value: string | number;
  color: string;
}) {
  return (
    <div className="bg-[#161b22] border border-[#30363d] rounded-xl p-5 flex items-center gap-4 hover:border-[#484f58] transition-colors">
      <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${color}`}>
        <Icon size={22} />
      </div>
      <div>
        <p className="text-[#8b949e] text-sm">{label}</p>
        <p className="text-white text-2xl font-bold">{value}</p>
      </div>
    </div>
  );
}

function ComparisonCard({ match }: { match: MatchedProduct }) {
  const cheaper = match.cheapest_source;
  const isMytekCheaper = cheaper === 'Mytek';
  const isTunisianetCheaper = cheaper === 'Tunisianet';
  const isSame = cheaper === 'Same';

  const winnerColor = isMytekCheaper
    ? 'border-emerald-500/50 shadow-emerald-500/10'
    : isTunisianetCheaper
    ? 'border-orange-500/50 shadow-orange-500/10'
    : 'border-yellow-500/50 shadow-yellow-500/10';

  return (
    <div className={`bg-[#161b22] border rounded-xl overflow-hidden shadow-lg hover:shadow-xl transition-all ${winnerColor}`}>
      {/* Header */}
      <div className="px-5 py-4 border-b border-[#30363d]">
        <h3 className="text-white font-semibold text-sm leading-relaxed line-clamp-2">
          {match.mytek_name}
        </h3>
        <div className="flex items-center gap-2 mt-2">
          <span className="text-xs text-[#8b949e] bg-[#21262d] px-2 py-0.5 rounded-full">
            {match.mytek_brand}
          </span>
          {match.tunisianet_discount && (
            <span className="text-xs text-orange-400 bg-orange-500/10 px-2 py-0.5 rounded-full flex items-center gap-1">
              <Zap size={10} />
              Promo
            </span>
          )}
          {match.savings_pct > 0 && (
            <span className="text-xs text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full flex items-center gap-1">
              <TrendingDown size={10} />
              Save {match.savings_pct}%
            </span>
          )}
        </div>
      </div>

      {/* Price Comparison */}
      <div className="grid grid-cols-2 divide-x divide-[#30363d]">
        {/* Mytek */}
        <div className={`p-4 ${isMytekCheaper ? 'bg-emerald-500/5' : isTunisianetCheaper ? 'bg-red-500/5' : 'bg-yellow-500/5'}`}>
          <div className="flex items-center gap-2 mb-2">
            <div className="w-6 h-6 rounded bg-[#0e4429] flex items-center justify-center">
              <span className="text-emerald-400 text-[10px] font-bold">M</span>
            </div>
            <span className="text-[#8b949e] text-xs font-medium">Mytek</span>
            {isMytekCheaper && (
              <span className="text-[10px] bg-emerald-500/20 text-emerald-400 px-1.5 py-0.5 rounded-full font-semibold">
                BEST
              </span>
            )}
          </div>
          <p className="text-white text-xl font-bold">{match.mytek_price_display}</p>
          <a
            href={match.mytek_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-[#58a6ff] hover:text-[#79c0ff] mt-2 flex items-center gap-1 transition-colors"
          >
            <ExternalLink size={10} /> Visit Mytek
          </a>
        </div>

        {/* Tunisianet */}
        <div className={`p-4 ${isTunisianetCheaper ? 'bg-emerald-500/5' : isMytekCheaper ? 'bg-red-500/5' : 'bg-yellow-500/5'}`}>
          <div className="flex items-center gap-2 mb-2">
            <div className="w-6 h-6 rounded bg-[#9e6a03] flex items-center justify-center">
              <span className="text-orange-400 text-[10px] font-bold">T</span>
            </div>
            <span className="text-[#8b949e] text-xs font-medium">Tunisianet</span>
            {isTunisianetCheaper && (
              <span className="text-[10px] bg-emerald-500/20 text-emerald-400 px-1.5 py-0.5 rounded-full font-semibold">
                BEST
              </span>
            )}
          </div>
          <p className="text-white text-xl font-bold">{match.tunisianet_price_display}</p>
          <a
            href={match.tunisianet_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-[#58a6ff] hover:text-[#79c0ff] mt-2 flex items-center gap-1 transition-colors"
          >
            <ExternalLink size={10} /> Visit Tunisianet
          </a>
        </div>
      </div>

      {/* Savings Banner */}
      {!isSame && (
        <div className={`px-5 py-3 flex items-center justify-between ${
          isMytekCheaper ? 'bg-emerald-500/10' : 'bg-emerald-500/10'
        }`}>
          <div className="flex items-center gap-2">
            <ShoppingCart size={14} className="text-emerald-400" />
            <span className="text-emerald-400 text-sm font-semibold">
              Buy at {cheaper} & save
            </span>
          </div>
          <span className="text-emerald-400 text-lg font-bold">
            {match.price_difference.toFixed(0)} TND
          </span>
        </div>
      )}
      {isSame && (
        <div className="px-5 py-3 bg-yellow-500/10 flex items-center justify-center">
          <span className="text-yellow-400 text-sm font-medium">
            Same price on both stores
          </span>
        </div>
      )}

      {/* Specs */}
      {(match.mytek_specs.ram || match.mytek_specs.processor) && (
        <div className="px-5 py-3 border-t border-[#30363d]">
          <div className="flex flex-wrap gap-2">
            {match.mytek_specs.ram && (
              <span className="text-[10px] text-[#8b949e] bg-[#21262d] px-2 py-1 rounded">
                {match.mytek_specs.ram}
              </span>
            )}
            {match.mytek_specs.screen && (
              <span className="text-[10px] text-[#8b949e] bg-[#21262d] px-2 py-1 rounded">
                {match.mytek_specs.screen}
              </span>
            )}
            {match.mytek_specs.storage && (
              <span className="text-[10px] text-[#8b949e] bg-[#21262d] px-2 py-1 rounded">
                {match.mytek_specs.storage}
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function SavingsCard({ match, rank }: { match: MatchedProduct; rank: number }) {
  return (
    <div className="bg-[#161b22] border border-[#30363d] rounded-xl p-4 flex items-center gap-4 hover:border-[#484f58] transition-colors">
      <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold ${
        rank === 1 ? 'bg-emerald-500 text-white' :
        rank === 2 ? 'bg-emerald-600 text-white' :
        rank === 3 ? 'bg-emerald-700 text-white' :
        'bg-[#21262d] text-[#8b949e]'
      }`}>
        {rank}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-white text-sm font-medium truncate">{match.mytek_name}</p>
        <p className="text-[#8b949e] text-xs mt-0.5">
          {match.cheapest_source} is cheaper
        </p>
      </div>
      <div className="text-right shrink-0">
        <p className="text-emerald-400 font-bold">{match.price_difference.toFixed(0)} TND</p>
        <p className="text-[#8b949e] text-xs">saved</p>
      </div>
    </div>
  );
}

export default function Home() {
  const { stats, loading, error, fuseReady, search, getTopSavings } = usePriceSearch();
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<MatchedProduct[]>([]);
  const [hasSearched, setHasSearched] = useState(false);
  const [showTopSavings, setShowTopSavings] = useState(true);

  const topSavings = useMemo(() => {
    if (!fuseReady) return [];
    return getTopSavings(10);
  }, [fuseReady, getTopSavings]);

  const handleSearch = (value: string) => {
    setQuery(value);
    if (value.trim().length >= 2) {
      const searchResults = search(value);
      setResults(searchResults);
      setHasSearched(true);
      setShowTopSavings(false);
    } else {
      setResults([]);
      setHasSearched(false);
      setShowTopSavings(true);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0d1117] flex items-center justify-center">
        <div className="text-center">
          <Monitor size={48} className="text-[#58a6ff] mx-auto mb-4 animate-pulse" />
          <p className="text-[#8b949e] text-lg">Loading price data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-[#0d1117] flex items-center justify-center">
        <div className="text-center max-w-md">
          <p className="text-red-400 text-lg mb-2">Something went wrong</p>
          <p className="text-[#8b949e]">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0d1117]">
      {/* Hero Section */}
      <div className="relative overflow-hidden">
        {/* Subtle gradient background */}
        <div className="absolute inset-0 bg-gradient-to-b from-[#161b22] via-[#0d1117] to-[#0d1117]" />
        <div className="absolute inset-0" style={{
          backgroundImage: 'radial-gradient(circle at 50% 0%, rgba(88, 166, 255, 0.08) 0%, transparent 50%)'
        }} />

        <div className="relative max-w-6xl mx-auto px-4 pt-16 pb-12">
          {/* Logo & Title */}
          <div className="text-center mb-10">
            <div className="inline-flex items-center gap-3 mb-4">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-[#58a6ff] to-[#388bfd] flex items-center justify-center shadow-lg shadow-blue-500/20">
                <Monitor size={24} className="text-white" />
              </div>
              <h1 className="text-3xl md:text-4xl font-bold text-white tracking-tight">
                Tunisia PC Price<span className="text-[#58a6ff]">Compare</span>
              </h1>
            </div>
            <p className="text-[#8b949e] text-lg max-w-xl mx-auto">
              Find the best laptop deals by comparing prices between Mytek and Tunisianet instantly.
            </p>
          </div>

          {/* Search Bar */}
          <div className="max-w-2xl mx-auto mb-12">
            <div className="relative">
              <Search size={20} className="absolute left-4 top-1/2 -translate-y-1/2 text-[#484f58]" />
              <input
                type="text"
                value={query}
                onChange={(e) => handleSearch(e.target.value)}
                placeholder="Search for a laptop model (e.g., Lenovo IdeaPad, HP Pavilion, Dell Vostro...)"
                className="w-full bg-[#161b22] border border-[#30363d] rounded-xl pl-12 pr-4 py-4 text-white placeholder-[#484f58] focus:outline-none focus:border-[#58a6ff] focus:ring-1 focus:ring-[#58a6ff] transition-all text-base shadow-lg"
              />
              {query && (
                <button
                  onClick={() => { setQuery(''); setResults([]); setHasSearched(false); setShowTopSavings(true); }}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-[#484f58] hover:text-white transition-colors"
                >
                  <ChevronDown size={18} className="rotate-180" />
                </button>
              )}
            </div>
            {hasSearched && results.length > 0 && (
              <p className="text-[#8b949e] text-sm mt-3 text-center">
                Found <span className="text-white font-semibold">{results.length}</span> matching products
              </p>
            )}
            {hasSearched && results.length === 0 && query.length >= 2 && (
              <p className="text-[#8b949e] text-sm mt-3 text-center">
                No results found. Try a different search term.
              </p>
            )}
          </div>

          {/* Stats */}
          {stats && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-4xl mx-auto">
              <StatCard
                icon={Package}
                label="Products Compared"
                value={stats.total_matched}
                color="bg-blue-500/10 text-blue-400"
              />
              <StatCard
                icon={Zap}
                label="Mytek Cheaper"
                value={stats.mytek_cheaper}
                color="bg-emerald-500/10 text-emerald-400"
              />
              <StatCard
                icon={Zap}
                label="Tunisianet Cheaper"
                value={stats.tunisianet_cheaper}
                color="bg-orange-500/10 text-orange-400"
              />
              <StatCard
                icon={TrendingDown}
                label="Max Savings"
                value={`${stats.max_savings.toFixed(0)} TND`}
                color="bg-purple-500/10 text-purple-400"
              />
            </div>
          )}
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-6xl mx-auto px-4 py-8">
        {/* Search Results */}
        {hasSearched && results.length > 0 && (
          <div className="mb-12">
            <h2 className="text-white text-xl font-bold mb-6 flex items-center gap-2">
              <Search size={20} className="text-[#58a6ff]" />
              Search Results
            </h2>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
              {results.map((match, i) => (
                <ComparisonCard key={`${match.mytek_url}-${i}`} match={match} />
              ))}
            </div>
          </div>
        )}

        {/* Top Savings */}
        {showTopSavings && topSavings.length > 0 && (
          <div className="mb-12">
            <h2 className="text-white text-xl font-bold mb-6 flex items-center gap-2">
              <BarChart3 size={20} className="text-[#58a6ff]" />
              Biggest Savings Right Now
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {topSavings.map((match, i) => (
                <SavingsCard key={i} match={match} rank={i + 1} />
              ))}
            </div>
          </div>
        )}

        {/* Popular Brands Quick Search */}
        {showTopSavings && (
          <div className="mb-12">
            <h2 className="text-white text-xl font-bold mb-6 flex items-center gap-2">
              <ArrowRight size={20} className="text-[#58a6ff]" />
              Popular Brands
            </h2>
            <div className="flex flex-wrap gap-3">
              {['LENOVO', 'HP', 'DELL', 'ASUS', 'ACER', 'APPLE', 'MSI'].map(brand => (
                <button
                  key={brand}
                  onClick={() => {
                    setQuery(brand);
                    handleSearch(brand);
                  }}
                  className="bg-[#161b22] border border-[#30363d] text-[#8b949e] px-5 py-2.5 rounded-lg hover:border-[#58a6ff] hover:text-white transition-all text-sm font-medium"
                >
                  {brand}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* How It Works */}
        <div className="mb-12">
          <h2 className="text-white text-xl font-bold mb-6">How It Works</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            <div className="bg-[#161b22] border border-[#30363d] rounded-xl p-5 text-center">
              <div className="w-12 h-12 rounded-full bg-[#21262d] flex items-center justify-center mx-auto mb-3">
                <Search size={20} className="text-[#58a6ff]" />
              </div>
              <h3 className="text-white font-semibold mb-2">Search</h3>
              <p className="text-[#8b949e] text-sm">Enter a laptop model or brand name to search our database.</p>
            </div>
            <div className="bg-[#161b22] border border-[#30363d] rounded-xl p-5 text-center">
              <div className="w-12 h-12 rounded-full bg-[#21262d] flex items-center justify-center mx-auto mb-3">
                <BarChart3 size={20} className="text-emerald-400" />
              </div>
              <h3 className="text-white font-semibold mb-2">Compare</h3>
              <p className="text-[#8b949e] text-sm">We instantly compare prices across Mytek and Tunisianet.</p>
            </div>
            <div className="bg-[#161b22] border border-[#30363d] rounded-xl p-5 text-center">
              <div className="w-12 h-12 rounded-full bg-[#21262d] flex items-center justify-center mx-auto mb-3">
                <ShoppingCart size={20} className="text-orange-400" />
              </div>
              <h3 className="text-white font-semibold mb-2">Save</h3>
              <p className="text-[#8b949e] text-sm">Buy from the cheaper store and save money on your next laptop.</p>
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="border-t border-[#30363d] bg-[#0d1117] py-8">
        <div className="max-w-6xl mx-auto px-4 text-center">
          <p className="text-[#484f58] text-sm">
            Tunisia PC PriceCompare — Compare laptop prices between Mytek.tn and Tunisianet.com.tn
          </p>
          <p className="text-[#30363d] text-xs mt-2">
            Prices are updated regularly. Always verify on the store before purchasing.
          </p>
        </div>
      </footer>
    </div>
  );
}
