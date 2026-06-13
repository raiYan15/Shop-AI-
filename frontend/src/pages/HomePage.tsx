import React, { useEffect } from 'react';
import { motion, useScroll, useTransform } from 'framer-motion';
import { Link } from 'react-router-dom';
import {
  Search, Brain, Star, MessageSquare, BarChart3,
  GitCompare, ChevronRight, Sparkles
} from 'lucide-react';
import { SearchBar } from '../components/ui/SearchBar';
import { FeatureCard } from '../components/ui/FeatureCard';
import { ProductCard } from '../components/ui/ProductCard';
import { Footer } from '../components/layout/Footer';
import { MOCK_PRODUCTS, CATEGORIES } from '../data/mockData';

const FEATURES = [
  { icon: Search, title: 'Semantic Search', description: 'Natural language search that understands what you mean, not just what you type. Powered by transformer models.', color: '#FF9900' },
  { icon: MessageSquare, title: 'AI Shopping Assistant', description: 'Get personalized advice from your AI shopping partner. Ask questions, compare products, get insights.', color: '#6366F1' },
  { icon: Brain, title: 'Smart Recommendations', description: 'ML-driven recommendations that learn your style, budget, and preferences over time.', color: '#10B981' },
  { icon: Star, title: 'Review Intelligence', description: 'AI distills thousands of reviews into actionable pros, cons, and sentiment scores instantly.', color: '#F59E0B' },
  { icon: GitCompare, title: 'Product Comparison', description: 'Side-by-side AI comparison across specs, performance, and value with visual scoring.', color: '#EF4444' },
  { icon: BarChart3, title: 'Explainable AI', description: 'Understand why a product was recommended with transparent AI reasoning and confidence scores.', color: '#8B5CF6' },
];

// Typing animation
const TypedText: React.FC = () => {
  const phrases = [
    'Best gaming laptop under ₹70,000',
    'Running shoes for beginners',
    'Phone with excellent camera',
    'Noise canceling headphones for work',
  ];
  const [phrase, setPhrase] = React.useState(0);
  const [displayed, setDisplayed] = React.useState('');
  const [deleting, setDeleting] = React.useState(false);

  useEffect(() => {
    const current = phrases[phrase];
    let timer: ReturnType<typeof setTimeout>;

    if (!deleting && displayed.length < current.length) {
      timer = setTimeout(() => setDisplayed(current.slice(0, displayed.length + 1)), 60);
    } else if (!deleting && displayed.length === current.length) {
      timer = setTimeout(() => setDeleting(true), 2000);
    } else if (deleting && displayed.length > 0) {
      timer = setTimeout(() => setDisplayed(displayed.slice(0, -1)), 30);
    } else if (deleting && displayed.length === 0) {
      setDeleting(false);
      setPhrase((prev) => (prev + 1) % phrases.length);
    }

    return () => clearTimeout(timer);
  }, [displayed, deleting, phrase]);

  return (
    <span style={{ color: 'rgba(255,255,255,0.35)', fontStyle: 'italic', fontFamily: 'JetBrains Mono, monospace', fontSize: 14 }}>
      e.g., "{displayed}
      <motion.span animate={{ opacity: [1, 0] }} transition={{ repeat: Infinity, duration: 0.7 }}>|</motion.span>
      "
    </span>
  );
};

export const HomePage: React.FC = () => {
  const { scrollY } = useScroll();
  const heroY = useTransform(scrollY, [0, 500], [0, 120]);
  const heroOpacity = useTransform(scrollY, [0, 300], [1, 0]);

  return (
    <div className="page-wrapper" style={{ paddingTop: 0 }}>
      {/* ===================== HERO ===================== */}
      <section style={{
        minHeight: '100vh',
        position: 'relative',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        overflow: 'hidden',
        background: `
          radial-gradient(ellipse 80% 50% at 50% -5%, rgba(255,153,0,0.12) 0%, transparent 60%),
          linear-gradient(180deg, #0D1117 0%, #131A22 100%)
        `,
      }}>
        {/* Precision grid overlay — enterprise aesthetic */}
        <div style={{
          position: 'absolute', inset: 0,
          backgroundImage: `
            linear-gradient(rgba(255,255,255,0.025) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255,255,255,0.025) 1px, transparent 1px)
          `,
          backgroundSize: '48px 48px',
          pointerEvents: 'none',
        }} />

        {/* Floating enterprise data panels — sharp rectangles */}
        <motion.div
          animate={{ y: [0, -10, 0] }}
          transition={{ duration: 6, repeat: Infinity, ease: 'easeInOut' }}
          style={{
            position: 'absolute', top: '18%', left: '4%',
            width: 164,
            background: 'rgba(22, 27, 34, 0.92)',
            border: '1px solid rgba(255,255,255,0.08)',
            borderTop: '2px solid #FF9900',
            /* SHARP — 0px, enterprise panel */
            borderRadius: 0,
            padding: '14px 16px',
            display: 'none',
          }}
          className="hero-float-card"
        >
          <div style={{ fontSize: 10, color: 'rgba(255,255,255,0.5)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.08em', fontFamily: 'JetBrains Mono, monospace', marginBottom: 8 }}>LIVE PICK</div>
          <div style={{ fontSize: 13, color: 'rgba(255,255,255,0.85)', fontWeight: 600, marginBottom: 4 }}>🎧 Sony XM5</div>
          <div style={{ fontSize: 11, color: '#FF9900', marginBottom: 4, fontFamily: 'JetBrains Mono, monospace' }}>AI SCORE: 96</div>
          <div style={{ fontSize: 17, fontWeight: 800, color: 'white', fontFamily: 'Outfit, sans-serif' }}>₹24,999</div>
        </motion.div>

        <motion.div
          animate={{ y: [0, 14, 0] }}
          transition={{ duration: 7, repeat: Infinity, ease: 'easeInOut', delay: 1 }}
          style={{
            position: 'absolute', top: '22%', right: '4%',
            width: 164,
            background: 'rgba(22, 27, 34, 0.92)',
            border: '1px solid rgba(255,255,255,0.08)',
            borderTop: '2px solid #6366F1',
            borderRadius: 0,
            padding: '14px 16px',
            display: 'none',
          }}
          className="hero-float-card"
        >
          <div style={{ fontSize: 10, color: 'rgba(255,255,255,0.5)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.08em', fontFamily: 'JetBrains Mono, monospace', marginBottom: 8 }}>TOP RATED</div>
          <div style={{ fontSize: 13, color: 'rgba(255,255,255,0.85)', fontWeight: 600, marginBottom: 4 }}>💻 ROG Strix G15</div>
          <div style={{ fontSize: 11, color: '#FF9900', marginBottom: 4, fontFamily: 'JetBrains Mono, monospace' }}>AI SCORE: 92</div>
          <div style={{ fontSize: 17, fontWeight: 800, color: 'white', fontFamily: 'Outfit, sans-serif' }}>₹67,999</div>
        </motion.div>

        {/* Content */}
        <motion.div
          style={{ y: heroY, opacity: heroOpacity }}
          className="container"
        >
          <div style={{ textAlign: 'center', maxWidth: 860, margin: '0 auto', padding: '120px 0 80px' }}>
            {/* Badge — sharp rectangular chip, not pill */}
            <motion.div
              initial={{ opacity: 0, y: -16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              style={{ marginBottom: 28, display: 'flex', justifyContent: 'center' }}
            >
              <div style={{
                display: 'inline-flex', alignItems: 'center', gap: 8,
                padding: '5px 14px',
                /* Sharp rectangle — NOT pill */
                borderRadius: 2,
                background: 'rgba(255,153,0,0.1)',
                border: '1px solid rgba(255,153,0,0.22)',
              }}>
                <Sparkles size={12} color="#FF9900" />
                <span style={{ fontSize: 12, fontWeight: 700, color: '#FF9900', textTransform: 'uppercase', letterSpacing: '0.08em', fontFamily: 'JetBrains Mono, monospace' }}>
                  Powered by Advanced AI • 2026 Edition
                </span>
              </div>
            </motion.div>

            {/* Headline */}
            <motion.h1
              initial={{ opacity: 0, y: 24 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.1 }}
              style={{
                fontFamily: 'Outfit, sans-serif',
                fontSize: 'clamp(40px, 7vw, 78px)',
                fontWeight: 900,
                color: 'white',
                lineHeight: 1.06,
                letterSpacing: '-0.04em',
                marginBottom: 22,
              }}
            >
              Discover Products{' '}
              <span style={{
                background: 'linear-gradient(135deg, #FF9900, #FFB84D)',
                WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
              }}>
                Smarter
              </span>{' '}
              with AI
            </motion.h1>

            {/* Subheadline */}
            <motion.p
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
              style={{
                fontSize: 'clamp(13px, 1.8vw, 17px)',
                color: 'rgba(255,255,255,0.45)',
                marginBottom: 14, lineHeight: 1.6,
                letterSpacing: '0.02em',
              }}
            >
              Semantic Search • Personalized Recommendations • AI Shopping Assistant • Explainable Rankings
            </motion.p>

            {/* Typed suggestion */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.3 }}
              style={{ fontSize: 14, marginBottom: 32, color: 'rgba(255,255,255,0.25)' }}
            >
              <TypedText />
            </motion.div>

            {/* Search Bar — AWS-style sharp search */}
            <motion.div
              initial={{ opacity: 0, y: 16, scale: 0.99 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              transition={{ duration: 0.5, delay: 0.3 }}
              style={{ marginBottom: 36 }}
            >
              <SearchBar size="hero" placeholder="Search anything — natural language supported..." />
            </motion.div>

            {/* CTA Buttons — sharp enterprise style */}
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.4 }}
              style={{ display: 'flex', gap: 12, justifyContent: 'center', flexWrap: 'wrap', marginBottom: 56 }}
            >
              <Link to="/assistant" className="btn-primary" style={{ fontSize: 15, padding: '13px 28px' }}>
                <MessageSquare size={16} />
                Try AI Assistant
              </Link>
              <Link to="/products" className="btn-secondary" style={{ color: 'rgba(255,255,255,0.7)', borderColor: 'rgba(255,255,255,0.18)', fontSize: 15, padding: '13px 28px' }}>
                Browse Products
                <ChevronRight size={15} />
              </Link>
            </motion.div>

            {/* Stats row — sharp divider between stats */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.6 }}
              style={{
                display: 'flex', gap: 0, justifyContent: 'center', flexWrap: 'wrap',
                border: '1px solid rgba(255,255,255,0.06)',
                borderRadius: 2,
                overflow: 'hidden',
                maxWidth: 480,
                margin: '0 auto',
              }}
            >
              {[
                { value: '2.4M+', label: 'Products' },
                { value: '98%', label: 'AI Accuracy' },
                { value: '150K+', label: 'Users' },
                { value: '4.9★', label: 'Rated' },
              ].map(({ value, label }, i) => (
                <div key={label} style={{
                  textAlign: 'center',
                  flex: 1,
                  padding: '16px 12px',
                  borderRight: i < 3 ? '1px solid rgba(255,255,255,0.06)' : 'none',
                }}>
                  <div style={{ fontSize: 20, fontWeight: 800, color: 'white', fontFamily: 'Outfit, sans-serif' }}>{value}</div>
                  <div style={{ fontSize: 10, color: 'rgba(255,255,255,0.35)', marginTop: 2, textTransform: 'uppercase', letterSpacing: '0.08em', fontFamily: 'JetBrains Mono, monospace' }}>{label}</div>
                </div>
              ))}
            </motion.div>
          </div>
        </motion.div>

        {/* Bottom fade */}
        <div style={{
          position: 'absolute', bottom: 0, left: 0, right: 0, height: 140,
          background: 'linear-gradient(transparent, var(--bg-primary))',
          pointerEvents: 'none',
        }} />
      </section>

      {/* ===================== FEATURES ===================== */}
      <section className="section" style={{ background: 'var(--bg-primary)' }}>
        <div className="container">
          <div style={{ textAlign: 'center', marginBottom: 56 }}>
            <div className="section-label">Platform Features</div>
            <h2 className="section-title" style={{ margin: '0 auto 14px' }}>
              AI-First Shopping{' '}
              <span style={{ color: '#FF9900' }}>Intelligence</span>
            </h2>
            <p className="section-subtitle" style={{ margin: '0 auto' }}>
              Every feature is designed with machine learning at its core — helping you discover, compare, and buy smarter.
            </p>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 20 }}>
            {FEATURES.map((feature, i) => (
              <FeatureCard key={feature.title} {...feature} index={i} />
            ))}
          </div>
        </div>
      </section>

      {/* ===================== RECOMMENDATIONS ===================== */}
      <section className="section" style={{ background: 'var(--bg-primary)' }}>
        <div className="container">
          {/* Recommended For You */}
          <div style={{ marginBottom: 56 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
              <div>
                <div className="section-label">AI Personalized</div>
                <h2 style={{ fontSize: 26, fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.02em' }}>
                  Recommended For You
                </h2>
              </div>
              <Link to="/recommendations" className="btn-secondary" style={{ fontSize: 13 }}>
                View All <ChevronRight size={13} />
              </Link>
            </div>
            <div className="scroll-container">
              {MOCK_PRODUCTS.slice(0, 6).map((product, i) => (
                <div key={product.id} style={{ minWidth: 280, maxWidth: 300 }}>
                  <ProductCard product={product} index={i} />
                </div>
              ))}
            </div>
          </div>

          {/* Trending */}
          <div style={{ marginBottom: 56 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
              <div>
                <div className="section-label">🔥 Hot Right Now</div>
                <h2 style={{ fontSize: 26, fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.02em' }}>
                  Trending Products
                </h2>
              </div>
              <Link to="/products" className="btn-secondary" style={{ fontSize: 13 }}>
                View All <ChevronRight size={13} />
              </Link>
            </div>
            <div className="scroll-container">
              {MOCK_PRODUCTS.slice(3, 9).map((product, i) => (
                <div key={product.id} style={{ minWidth: 280, maxWidth: 300 }}>
                  <ProductCard product={product} index={i} />
                </div>
              ))}
            </div>
          </div>

          {/* Categories — sharp rectangular grid */}
          <div>
            <div style={{ textAlign: 'center', marginBottom: 32 }}>
              <div className="section-label">Browse by Category</div>
              <h2 style={{ fontSize: 26, fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.02em' }}>
                Shop by Category
              </h2>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))', gap: 12 }}>
              {CATEGORIES.map((cat, i) => (
                <motion.div
                  key={cat.name}
                  initial={{ opacity: 0, scale: 0.95 }}
                  whileInView={{ opacity: 1, scale: 1 }}
                  viewport={{ once: true }}
                  transition={{ delay: i * 0.05 }}
                  whileHover={{ y: -4 }}
                >
                  <Link to="/products" style={{ textDecoration: 'none' }}>
                    <div
                      style={{
                        background: 'var(--bg-card)',
                        border: '1px solid var(--border-color)',
                        /* Sharp — 2px max */
                        borderRadius: 2,
                        padding: '22px 14px',
                        textAlign: 'center',
                        cursor: 'pointer',
                        transition: 'border-color 0.15s, box-shadow 0.15s',
                        boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
                      }}
                      onMouseEnter={(e) => {
                        (e.currentTarget as HTMLElement).style.borderColor = 'rgba(255,153,0,0.4)';
                        (e.currentTarget as HTMLElement).style.borderTopColor = '#FF9900';
                        (e.currentTarget as HTMLElement).style.boxShadow = '0 4px 16px rgba(0,0,0,0.1)';
                      }}
                      onMouseLeave={(e) => {
                        (e.currentTarget as HTMLElement).style.borderColor = 'var(--border-color)';
                        (e.currentTarget as HTMLElement).style.boxShadow = '0 1px 3px rgba(0,0,0,0.06)';
                      }}
                    >
                      <div style={{ fontSize: 28, marginBottom: 8 }}>{cat.icon}</div>
                      <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 3 }}>{cat.name}</div>
                      <div style={{ fontSize: 10, color: 'var(--text-secondary)', fontFamily: 'JetBrains Mono, monospace' }}>{cat.count} items</div>
                    </div>
                  </Link>
                </motion.div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ===================== CTA BANNER ===================== */}
      <section style={{ padding: '80px 0' }}>
        <div className="container">
          <motion.div
            initial={{ opacity: 0, y: 24 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            style={{
              /* Sharp rectangular CTA banner — NOT rounded card */
              borderRadius: 2,
              padding: '60px 48px',
              background: 'linear-gradient(135deg, #0D1117 0%, #1C2331 100%)',
              border: '1px solid rgba(255,153,0,0.18)',
              borderLeft: '4px solid #FF9900',
              textAlign: 'center',
              position: 'relative',
              overflow: 'hidden',
            }}
          >
            {/* Grid overlay */}
            <div style={{
              position: 'absolute', inset: 0,
              backgroundImage: `
                linear-gradient(rgba(255,255,255,0.015) 1px, transparent 1px),
                linear-gradient(90deg, rgba(255,255,255,0.015) 1px, transparent 1px)
              `,
              backgroundSize: '48px 48px',
              pointerEvents: 'none',
            }} />

            <h2 style={{
              fontFamily: 'Outfit, sans-serif', fontWeight: 900,
              fontSize: 'clamp(26px, 5vw, 46px)',
              color: 'white', marginBottom: 14, position: 'relative',
              letterSpacing: '-0.03em',
            }}>
              Ready to shop with{' '}
              <span style={{ color: '#FF9900' }}>superintelligence?</span>
            </h2>
            <p style={{ color: 'rgba(255,255,255,0.45)', fontSize: 17, marginBottom: 32, position: 'relative' }}>
              Join 150,000+ users who shop smarter with ShopMind AI.
            </p>
            <div style={{ display: 'flex', gap: 12, justifyContent: 'center', flexWrap: 'wrap', position: 'relative' }}>
              <Link to="/assistant" className="btn-primary" style={{ fontSize: 15, padding: '13px 28px' }}>
                <Sparkles size={16} />
                Start for Free
              </Link>
              <Link to="/products" className="btn-secondary" style={{ color: 'rgba(255,255,255,0.65)', borderColor: 'rgba(255,255,255,0.18)', padding: '13px 28px', fontSize: 15 }}>
                Explore Products
              </Link>
            </div>
          </motion.div>
        </div>
      </section>

      <Footer />

      <style>{`
        @media (min-width: 900px) { .hero-float-card { display: block !important; } }
      `}</style>
    </div>
  );
};
