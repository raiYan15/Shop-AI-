import React, { useEffect, useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import { Sparkles, Brain, Database, Activity, RefreshCcw, AlertTriangle, Zap } from 'lucide-react';

import { Footer } from '../components/layout/Footer';
import { ProductCard } from '../components/ui/ProductCard';
import { Product } from '../data/mockData';
import {
  HybridRecommendationBundle,
  HybridRecommendationInsight,
  HybridRecommendationItem,
  getHybridRecommendations,
} from '../services/api';
import { useStore } from '../store/useStore';
import { liveProductToCard } from '../utils/productMapper';

const COUNTRIES = ['US', 'IN', 'GB', 'DE', 'JP'];

const toCard = (item: HybridRecommendationItem): Product => {
  const mapped = liveProductToCard(item);
  const aiScore = Math.max(0, Math.min(100, Math.round(item.ai_match ?? mapped.aiScore)));
  return {
    ...mapped,
    aiScore,
    badge: item.is_new_arrival ? 'NEW ARRIVAL' : mapped.badge,
  };
};

const safeCards = (items: HybridRecommendationItem[]) => items.map(toCard);

const StatChip: React.FC<{ label: string; value: string; icon: React.ReactNode; accent: string }> = ({
  label,
  value,
  icon,
  accent,
}) => (
  <div
    style={{
      border: '1px solid var(--border-color)',
      borderLeft: `3px solid ${accent}`,
      borderRadius: 2,
      background: 'var(--bg-card)',
      padding: '12px 14px',
      minWidth: 180,
      display: 'flex',
      alignItems: 'center',
      gap: 10,
    }}
  >
    <div
      style={{
        width: 30,
        height: 30,
        borderRadius: 2,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: `${accent}15`,
      }}
    >
      {icon}
    </div>
    <div>
      <div style={{ fontSize: 17, fontWeight: 800, color: 'var(--text-primary)' }}>{value}</div>
      <div
        style={{
          fontSize: 10,
          color: 'var(--text-secondary)',
          textTransform: 'uppercase',
          letterSpacing: '0.08em',
          fontFamily: 'JetBrains Mono, monospace',
        }}
      >
        {label}
      </div>
    </div>
  </div>
);

const SectionHeader: React.FC<{ title: string; subtitle?: string }> = ({ title, subtitle }) => (
  <div style={{ marginBottom: 14, display: 'flex', alignItems: 'end', justifyContent: 'space-between', gap: 12 }}>
    <div>
      <h2 style={{ margin: 0, fontSize: 22, fontWeight: 800, color: 'var(--text-primary)' }}>{title}</h2>
      {subtitle ? <p style={{ margin: '5px 0 0', color: 'var(--text-secondary)', fontSize: 13 }}>{subtitle}</p> : null}
    </div>
  </div>
);

export const RecommendationsPage: React.FC = () => {
  const currentUser = useStore((s) => s.currentUser);
  const [country, setCountry] = useState('US');
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [bundle, setBundle] = useState<HybridRecommendationBundle | null>(null);

  const userId = currentUser?.id || 'guest';

  const load = async (isManualRefresh = false) => {
    if (isManualRefresh) setRefreshing(true);
    else setLoading(true);

    try {
      setError(null);
      const payload = await getHybridRecommendations(userId, 12, country);
      setBundle(payload);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load recommendations');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    void load(false);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [country, userId]);

  const hybridCards = useMemo(() => safeCards(bundle?.sections.hybrid_recommendations ?? []), [bundle]);
  const newCards = useMemo(() => safeCards(bundle?.sections.new_products ?? []), [bundle]);
  const similarCards = useMemo(() => safeCards(bundle?.sections.similar_products ?? []), [bundle]);
  const trendingCards = useMemo(() => safeCards(bundle?.sections.trending_ai_students ?? []), [bundle]);
  const insights: HybridRecommendationInsight[] = bundle?.sections.ai_product_insights ?? [];

  return (
    <div className="page-wrapper">
      <div style={{ background: 'linear-gradient(180deg, #0D1117 0%, var(--bg-primary) 100%)', paddingBottom: 46 }}>
        <div className="container" style={{ paddingTop: 42 }}>
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}>
            <div className="section-label">Recommended For You • Powered by ShopMind AI</div>
            <h1 className="section-title" style={{ color: 'white', marginBottom: 10 }}>
              Hybrid AI Recommendation Engine
            </h1>
            <p style={{ color: 'rgba(255,255,255,0.55)', maxWidth: 880, margin: 0 }}>
              Historical dataset intelligence + live Amazon product feed + semantic retrieval + FAISS vector similarity + AI ranking.
            </p>
          </motion.div>

          <div style={{ marginTop: 20, display: 'flex', flexWrap: 'wrap', gap: 10, alignItems: 'center' }}>
            <label htmlFor="recommendation-country" style={{ color: 'rgba(255,255,255,0.85)', fontSize: 12, fontWeight: 700 }}>
              Live Country
            </label>
            <select
              id="recommendation-country"
              value={country}
              onChange={(e) => setCountry(e.target.value)}
              style={{
                border: '1px solid rgba(255,255,255,0.2)',
                borderRadius: 2,
                background: 'rgba(255,255,255,0.08)',
                color: 'white',
                padding: '8px 10px',
                fontSize: 12,
                fontFamily: 'JetBrains Mono, monospace',
              }}
            >
              {COUNTRIES.map((c) => (
                <option key={c} value={c} style={{ color: 'black' }}>
                  {c}
                </option>
              ))}
            </select>

            <button
              type="button"
              onClick={() => void load(true)}
              style={{
                border: '1px solid rgba(255,255,255,0.24)',
                borderRadius: 2,
                background: 'rgba(255,153,0,0.14)',
                color: 'white',
                padding: '8px 12px',
                fontSize: 12,
                fontWeight: 700,
                display: 'inline-flex',
                alignItems: 'center',
                gap: 6,
                cursor: 'pointer',
              }}
            >
              <RefreshCcw size={14} /> {refreshing ? 'Refreshing…' : 'Refresh Hybrid Feed'}
            </button>
          </div>

          <div style={{ marginTop: 22, display: 'flex', gap: 10, flexWrap: 'wrap' }}>
            <StatChip
              label="Products Analyzed"
              value={String(bundle?.summary.products_analyzed ?? 0)}
              icon={<Database size={14} color="#FF9900" />}
              accent="#FF9900"
            />
            <StatChip
              label="AI Accuracy"
              value={`${bundle?.summary.ai_accuracy ?? 0}%`}
              icon={<Brain size={14} color="#7C3AED" />}
              accent="#7C3AED"
            />
            <StatChip
              label="Live Product Count"
              value={String(bundle?.summary.live_product_count ?? 0)}
              icon={<Activity size={14} color="#10B981" />}
              accent="#10B981"
            />
            <StatChip
              label="Last Update"
              value={bundle?.summary.last_update_time ? new Date(bundle.summary.last_update_time).toLocaleTimeString() : '--'}
              icon={<Sparkles size={14} color="#06B6D4" />}
              accent="#06B6D4"
            />
          </div>
        </div>
      </div>

      <div className="container" style={{ paddingTop: 24, paddingBottom: 70 }}>
        {loading ? (
          <div style={{ border: '1px solid var(--border-color)', borderRadius: 2, background: 'var(--bg-card)', padding: 18 }}>
            Loading hybrid recommendations…
          </div>
        ) : null}

        {error ? (
          <div
            style={{
              border: '1px solid rgba(220,38,38,0.25)',
              background: 'rgba(220,38,38,0.08)',
              borderRadius: 2,
              padding: 12,
              marginBottom: 16,
              display: 'flex',
              alignItems: 'center',
              gap: 8,
            }}
          >
            <AlertTriangle size={14} color="#ef4444" />
            <span style={{ fontSize: 13, color: 'var(--text-primary)' }}>{error}</span>
          </div>
        ) : null}

        {!loading && !error ? (
          <>
            <section style={{ marginBottom: 30 }}>
              <SectionHeader title="Hybrid Recommendations" subtitle="AI Recommended" />
              <div className="grid-auto">
                {hybridCards.map((p, idx) => (
                  <ProductCard key={`${p.id}-${idx}`} product={p} index={idx} />
                ))}
              </div>
            </section>

            <section style={{ marginBottom: 30 }}>
              <SectionHeader title="New Products You May Like" subtitle="Discovered from Live Amazon API" />
              <div className="grid-auto">
                {newCards.map((p, idx) => (
                  <ProductCard key={`new-${p.id}-${idx}`} product={p} index={idx} />
                ))}
              </div>
            </section>

            <section style={{ marginBottom: 30 }}>
              <SectionHeader title="Similar Products" subtitle="Powered by FAISS Similarity Search" />
              <div className="grid-auto">
                {similarCards.map((p, idx) => (
                  <ProductCard key={`sim-${p.id}-${idx}`} product={p} index={idx} />
                ))}
              </div>
            </section>

            <section style={{ marginBottom: 30 }}>
              <SectionHeader title="Trending Among AI Students" subtitle="Search trends + popularity + ratings + activity" />
              <div className="grid-auto">
                {trendingCards.map((p, idx) => (
                  <ProductCard key={`trend-${p.id}-${idx}`} product={p} index={idx} />
                ))}
              </div>
            </section>

            <section>
              <SectionHeader title="AI Product Insights" subtitle="Pros, Cons, Best Use Cases, Value For Money, Recommendation Confidence" />
              <div style={{ display: 'grid', gap: 12 }}>
                {insights.map((insight) => (
                  <div
                    key={insight.product_id}
                    style={{
                      border: '1px solid var(--border-color)',
                      borderRadius: 2,
                      background: 'var(--bg-card)',
                      padding: 14,
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8, marginBottom: 8 }}>
                      <h3 style={{ margin: 0, fontSize: 15, color: 'var(--text-primary)' }}>{insight.product_name}</h3>
                      <span
                        style={{
                          fontFamily: 'JetBrains Mono, monospace',
                          fontSize: 11,
                          fontWeight: 700,
                          color: '#FF9900',
                          border: '1px solid rgba(255,153,0,0.25)',
                          padding: '2px 7px',
                          borderRadius: 2,
                        }}
                      >
                        <Zap size={12} style={{ marginRight: 5, verticalAlign: 'text-bottom' }} />
                        {insight.recommendation_confidence}% confidence
                      </span>
                    </div>
                    <div style={{ display: 'grid', gap: 10, gridTemplateColumns: 'repeat(auto-fit,minmax(220px,1fr))' }}>
                      <div>
                        <strong style={{ fontSize: 12 }}>Pros</strong>
                        <ul style={{ margin: '6px 0 0', paddingLeft: 16, fontSize: 12 }}>
                          {insight.pros.map((p) => (
                            <li key={p}>{p}</li>
                          ))}
                        </ul>
                      </div>
                      <div>
                        <strong style={{ fontSize: 12 }}>Cons</strong>
                        <ul style={{ margin: '6px 0 0', paddingLeft: 16, fontSize: 12 }}>
                          {insight.cons.map((p) => (
                            <li key={p}>{p}</li>
                          ))}
                        </ul>
                      </div>
                      <div>
                        <strong style={{ fontSize: 12 }}>Best Use Cases</strong>
                        <ul style={{ margin: '6px 0 0', paddingLeft: 16, fontSize: 12 }}>
                          {insight.best_use_cases.map((p) => (
                            <li key={p}>{p}</li>
                          ))}
                        </ul>
                      </div>
                      <div>
                        <strong style={{ fontSize: 12 }}>Value For Money</strong>
                        <p style={{ margin: '6px 0 0', fontSize: 13, fontWeight: 700, color: '#10B981' }}>
                          {insight.value_for_money_score}%
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          </>
        ) : null}
      </div>

      <Footer />
    </div>
  );
};
