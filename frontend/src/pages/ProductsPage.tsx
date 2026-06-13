import React, { useState, useMemo, useEffect } from 'react';
import { motion } from 'framer-motion';
import { SlidersHorizontal, Grid3X3, List, Search, Loader2, RefreshCw } from 'lucide-react';
import { ProductCard } from '../components/ui/ProductCard';
import { Footer } from '../components/layout/Footer';
import { MOCK_PRODUCTS, CATEGORIES, Product } from '../data/mockData';
import { useStore } from '../store/useStore';
import { getAmazonProductCategoryList, getLiveProducts, searchProducts } from '../services/api';
import { liveProductToCard } from '../utils/productMapper';

type SortOption = 'relevance' | 'price-asc' | 'price-desc' | 'rating' | 'ai-score';

export const ProductsPage: React.FC = () => {
  const { searchQuery, activeCategory, setActiveCategory } = useStore();
  const [sortBy, setSortBy] = useState<SortOption>('relevance');
  const [layout, setLayout] = useState<'grid' | 'list'>('grid');
  const [priceRange, setPriceRange] = useState<[number, number]>([0, 200000]);
  const [minRating, setMinRating] = useState(0);
  const [showFilters, setShowFilters] = useState(false);
  const [liveProducts, setLiveProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [usingLiveData, setUsingLiveData] = useState(false);
  const [taxonomyCountry, setTaxonomyCountry] = useState('US');
  const [taxonomyOptions, setTaxonomyOptions] = useState<string[]>([]);
  const [taxonomyLoading, setTaxonomyLoading] = useState(false);
  const [taxonomyError, setTaxonomyError] = useState('');
  const [selectedTaxonomy, setSelectedTaxonomy] = useState('All Amazon Categories');

  const extractCategoryNames = (payload: unknown): string[] => {
    const names: string[] = [];

    const walk = (node: unknown) => {
      if (!node) return;
      if (Array.isArray(node)) {
        for (const item of node) walk(item);
        return;
      }
      if (typeof node === 'object') {
        const obj = node as Record<string, unknown>;
        const candidateKeys = ['category_name', 'name', 'display_name', 'title'];
        for (const key of candidateKeys) {
          const value = obj[key];
          if (typeof value === 'string') {
            const clean = value.trim();
            if (clean.length > 1 && clean.length < 80) names.push(clean);
          }
        }
        for (const value of Object.values(obj)) walk(value);
      }
    };

    walk(payload);
    return [...new Set(names)].slice(0, 200);
  };

  const loadTaxonomies = async () => {
    setTaxonomyLoading(true);
    setTaxonomyError('');
    try {
      const res = await getAmazonProductCategoryList(taxonomyCountry);
      const names = extractCategoryNames(res.data);
      setTaxonomyOptions(names);
      if (names.length === 0) {
        setTaxonomyError('No Amazon categories found for selected country.');
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to fetch Amazon taxonomy.';
      setTaxonomyError(message);
      setTaxonomyOptions([]);
    } finally {
      setTaxonomyLoading(false);
    }
  };

  useEffect(() => {
    let cancelled = false;

    async function fetchProducts() {
      setLoading(true);
      try {
        if (searchQuery.trim()) {
          const result = await searchProducts(searchQuery, 40);
          if (!cancelled && result.results.length > 0) {
            setLiveProducts(result.results.map((p) => liveProductToCard({
              product_id: p.product_id,
              product_name: p.product_name,
              category: p.category,
              price: p.price,
              rating: p.rating,
              rating_count: p.rating_count,
              ai_match: p.score ?? (p.similarity_score ? p.similarity_score * 100 : 0),
              similarity_score: p.similarity_score,
            })));
            setUsingLiveData(true);
            return;
          }
        }

        const page = await getLiveProducts(
          1,
          40,
          activeCategory !== 'All' ? activeCategory.toLowerCase() : undefined,
          'updated_at'
        );
        if (!cancelled && page.products.length > 0) {
          setLiveProducts(page.products.map(liveProductToCard));
          setUsingLiveData(true);
          return;
        }
      } catch {
        /* fall back to mock */
      }
      if (!cancelled) {
        setLiveProducts(MOCK_PRODUCTS);
        setUsingLiveData(false);
      }
      if (!cancelled) setLoading(false);
    }

    fetchProducts().finally(() => {
      if (!cancelled) setLoading(false);
    });

    return () => { cancelled = true; };
  }, [searchQuery, activeCategory]);

  useEffect(() => {
    loadTaxonomies();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [taxonomyCountry]);

  const sourceProducts = usingLiveData ? liveProducts : MOCK_PRODUCTS;

  const filteredProducts = useMemo(() => {
    let products = [...sourceProducts];

    if (activeCategory !== 'All') {
      products = products.filter((p) => p.category === activeCategory);
    }
    if (selectedTaxonomy !== 'All Amazon Categories') {
      const tax = selectedTaxonomy.toLowerCase();
      products = products.filter((p) =>
        p.category.toLowerCase().includes(tax) ||
        p.name.toLowerCase().includes(tax) ||
        p.description.toLowerCase().includes(tax)
      );
    }
    if (searchQuery && !usingLiveData) {
      const q = searchQuery.toLowerCase();
      products = products.filter(
        (p) =>
          p.name.toLowerCase().includes(q) ||
          p.category.toLowerCase().includes(q) ||
          p.brand.toLowerCase().includes(q) ||
          p.description.toLowerCase().includes(q)
      );
    }
    products = products.filter((p) => p.price >= priceRange[0] && p.price <= priceRange[1]);
    if (minRating > 0) {
      products = products.filter((p) => p.rating >= minRating);
    }
    switch (sortBy) {
      case 'price-asc': products.sort((a, b) => a.price - b.price); break;
      case 'price-desc': products.sort((a, b) => b.price - a.price); break;
      case 'rating': products.sort((a, b) => b.rating - a.rating); break;
      case 'ai-score': products.sort((a, b) => b.aiScore - a.aiScore); break;
    }
    return products;
  }, [sourceProducts, searchQuery, activeCategory, selectedTaxonomy, sortBy, priceRange, minRating, usingLiveData]);

  const allCategories = ['All', ...CATEGORIES.map((c) => c.name)];

  return (
    <div className="page-wrapper">
      <div style={{ background: 'linear-gradient(180deg, #0D1117, var(--bg-primary))', paddingBottom: 36 }}>
        <div className="container" style={{ paddingTop: 40 }}>
          <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}>
            <div className="section-label">Browse & Discover</div>
            <h1 className="section-title" style={{ marginBottom: 6 }}>
              {searchQuery ? `Results for "${searchQuery}"` : 'All Products'}
            </h1>
            <p style={{ color: 'var(--text-secondary)', fontSize: 14, fontFamily: 'JetBrains Mono, monospace' }}>
              {filteredProducts.length} products • {usingLiveData ? 'Live catalog' : 'Demo catalog'} • AI-ranked
            </p>
          </motion.div>

          {/* Category Filter — sharp rectangular chips, NOT pills */}
          <div style={{ display: 'flex', gap: 6, overflowX: 'auto', padding: '20px 0', scrollbarWidth: 'none' }}>
            {allCategories.map((cat) => (
              <motion.button
                key={cat}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.97 }}
                onClick={() => setActiveCategory(cat)}
                style={{
                  padding: '7px 16px',
                  /* SHARP rectangle — NOT pill (no border-radius: 999px) */
                  borderRadius: 2,
                  border: activeCategory === cat
                    ? '1px solid #FF9900'
                    : '1px solid var(--border-color)',
                  background: activeCategory === cat
                    ? '#FF9900'
                    : 'var(--bg-card)',
                  color: activeCategory === cat ? '#0D1117' : 'var(--text-secondary)',
                  fontWeight: 700, fontSize: 12, cursor: 'pointer',
                  whiteSpace: 'nowrap',
                  transition: 'all 0.15s',
                  textTransform: 'uppercase',
                  letterSpacing: '0.04em',
                  fontFamily: 'Inter, sans-serif',
                }}
              >
                {cat}
              </motion.button>
            ))}
          </div>

          {/* Toolbar — enterprise control bar */}
          <div style={{
            display: 'flex', gap: 10, alignItems: 'center',
            justifyContent: 'space-between', flexWrap: 'wrap',
            padding: '12px 16px',
            background: 'var(--bg-card)',
            border: '1px solid var(--border-color)',
            borderRadius: 2,
          }}>
            <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              <motion.button
                whileTap={{ scale: 0.97 }}
                onClick={() => setShowFilters(!showFilters)}
                style={{
                  display: 'flex', alignItems: 'center', gap: 6,
                  padding: '7px 14px',
                  /* Sharp */
                  borderRadius: 2,
                  border: '1px solid var(--border-color)',
                  background: showFilters ? 'rgba(255,153,0,0.1)' : 'transparent',
                  color: showFilters ? '#FF9900' : 'var(--text-secondary)',
                  fontSize: 12, fontWeight: 600, cursor: 'pointer',
                  textTransform: 'uppercase',
                  letterSpacing: '0.04em',
                }}
              >
                <SlidersHorizontal size={13} />
                Filters
              </motion.button>

              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as SortOption)}
                style={{
                  padding: '7px 12px',
                  /* Sharp */
                  borderRadius: 2,
                  border: '1px solid var(--border-color)',
                  background: 'var(--bg-card)', color: 'var(--text-primary)',
                  fontSize: 12, fontWeight: 600, cursor: 'pointer',
                  outline: 'none',
                }}
              >
                <option value="relevance">AI Relevance</option>
                <option value="ai-score">AI Score</option>
                <option value="rating">Top Rated</option>
                <option value="price-asc">Price: Low → High</option>
                <option value="price-desc">Price: High → Low</option>
              </select>
            </div>

            <div style={{ display: 'flex', gap: 2 }}>
              {[
                { view: 'grid', icon: Grid3X3 },
                { view: 'list', icon: List },
              ].map(({ view, icon: Icon }) => (
                <button
                  key={view}
                  onClick={() => setLayout(view as 'grid' | 'list')}
                  style={{
                    width: 33, height: 33,
                    /* Sharp */
                    borderRadius: 2,
                    border: '1px solid var(--border-color)',
                    background: layout === view ? 'rgba(255,153,0,0.1)' : 'transparent',
                    color: layout === view ? '#FF9900' : 'var(--text-secondary)',
                    cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center',
                    transition: 'all 0.15s',
                  }}
                >
                  <Icon size={14} />
                </button>
              ))}
            </div>
          </div>

          {/* Filter Panel — sharp rectangular panel */}
          {showFilters && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              style={{
                background: 'var(--bg-card)',
                border: '1px solid var(--border-color)',
                borderTop: '2px solid #FF9900',
                /* Sharp panel */
                borderRadius: 2,
                padding: '20px 24px',
                marginTop: 8,
                display: 'flex', gap: 32, flexWrap: 'wrap',
              }}
            >
              <div>
                <label style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-primary)', display: 'block', marginBottom: 10, textTransform: 'uppercase', letterSpacing: '0.06em', fontFamily: 'JetBrains Mono, monospace' }}>
                  Min Rating: {minRating}★
                </label>
                <input
                  type="range" min={0} max={5} step={0.5} value={minRating}
                  onChange={(e) => setMinRating(+e.target.value)}
                  style={{ width: 180, accentColor: '#FF9900' }}
                />
              </div>
              <div>
                <label style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-primary)', display: 'block', marginBottom: 10, textTransform: 'uppercase', letterSpacing: '0.06em', fontFamily: 'JetBrains Mono, monospace' }}>
                  Max Price: ₹{priceRange[1].toLocaleString('en-IN')}
                </label>
                <input
                  type="range" min={0} max={200000} step={5000} value={priceRange[1]}
                  onChange={(e) => setPriceRange([priceRange[0], +e.target.value])}
                  style={{ width: 180, accentColor: '#FF9900' }}
                />
              </div>

              <div style={{ minWidth: 260 }}>
                <label style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-primary)', display: 'block', marginBottom: 10, textTransform: 'uppercase', letterSpacing: '0.06em', fontFamily: 'JetBrains Mono, monospace' }}>
                  Amazon Taxonomy
                </label>
                <div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
                  <select
                    title="Amazon taxonomy country"
                    value={taxonomyCountry}
                    onChange={(e) => setTaxonomyCountry(e.target.value)}
                    style={{
                      padding: '6px 10px',
                      borderRadius: 2,
                      border: '1px solid var(--border-color)',
                      background: 'var(--bg-card)',
                      color: 'var(--text-primary)',
                      fontSize: 12,
                      fontWeight: 600,
                      fontFamily: 'JetBrains Mono, monospace',
                    }}
                  >
                    <option value="US">US</option>
                    <option value="IN">IN</option>
                    <option value="GB">GB</option>
                    <option value="DE">DE</option>
                    <option value="JP">JP</option>
                  </select>
                  <button
                    title="Refresh Amazon taxonomy"
                    onClick={loadTaxonomies}
                    disabled={taxonomyLoading}
                    style={{
                      width: 30,
                      height: 30,
                      borderRadius: 2,
                      border: '1px solid var(--border-color)',
                      background: 'transparent',
                      color: taxonomyLoading ? 'var(--text-secondary)' : '#FF9900',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      cursor: taxonomyLoading ? 'not-allowed' : 'pointer',
                    }}
                  >
                    <RefreshCw size={13} style={{ animation: taxonomyLoading ? 'spin 1s linear infinite' : 'none' }} />
                  </button>
                </div>
                <select
                  title="Amazon category filter"
                  value={selectedTaxonomy}
                  onChange={(e) => setSelectedTaxonomy(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '7px 10px',
                    borderRadius: 2,
                    border: '1px solid var(--border-color)',
                    background: 'var(--bg-card)',
                    color: 'var(--text-primary)',
                    fontSize: 12,
                    fontWeight: 600,
                    outline: 'none',
                  }}
                >
                  <option value="All Amazon Categories">All Amazon Categories</option>
                  {taxonomyOptions.map((cat) => (
                    <option key={cat} value={cat}>{cat}</option>
                  ))}
                </select>
                {taxonomyError && (
                  <p style={{ marginTop: 6, fontSize: 11, color: '#EF4444' }}>{taxonomyError}</p>
                )}
              </div>

              <button
                onClick={() => {
                  setMinRating(0);
                  setPriceRange([0, 200000]);
                  setActiveCategory('All');
                  setSelectedTaxonomy('All Amazon Categories');
                }}
                style={{
                  padding: '7px 14px',
                  /* Sharp reset button */
                  borderRadius: 2,
                  background: 'rgba(239,68,68,0.08)',
                  border: '1px solid rgba(239,68,68,0.2)',
                  color: '#EF4444', fontSize: 12, fontWeight: 700, cursor: 'pointer',
                  alignSelf: 'flex-end',
                  textTransform: 'uppercase',
                  letterSpacing: '0.04em',
                }}
              >
                Reset Filters
              </button>
            </motion.div>
          )}
        </div>
      </div>

      {/* Products Grid */}
      <div className="container" style={{ paddingTop: 28, paddingBottom: 60 }}>
        {loading ? (
          <div style={{ textAlign: 'center', padding: '72px 0' }}>
            <Loader2 size={36} color="#FF9900" style={{ animation: 'spin 1s linear infinite', marginBottom: 14 }} />
            <p style={{ color: 'var(--text-secondary)', fontSize: 14 }}>Loading live products from ShopMind AI …</p>
          </div>
        ) : filteredProducts.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '72px 0' }}>
            <Search size={44} color="var(--text-secondary)" style={{ opacity: 0.25, marginBottom: 14 }} />
            <h3 style={{ fontSize: 20, color: 'var(--text-primary)', marginBottom: 6 }}>No products found</h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: 14 }}>Try adjusting your filters or search query</p>
          </div>
        ) : (
          <div className="grid-auto">
            {filteredProducts.map((product, i) => (
              <ProductCard key={product.id} product={product} index={i} />
            ))}
          </div>
        )}
      </div>

      <Footer />
    </div>
  );
};
