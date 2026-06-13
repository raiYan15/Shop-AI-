import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Brain, ThumbsUp, ThumbsDown, Zap, BarChart2, CheckCircle, XCircle } from 'lucide-react';
import { Product } from '../../data/mockData';

interface AiInsightsPanelProps {
  product: Product;
}

const AnimatedGauge: React.FC<{ score: number }> = ({ score }) => {
  const [animated, setAnimated] = useState(false);
  const [displayScore, setDisplayScore] = useState(0);
  useEffect(() => {
    setTimeout(() => setAnimated(true), 300);
    let current = 0;
    const step = score / 60;
    const timer = setInterval(() => {
      current = Math.min(current + step, score);
      setDisplayScore(Math.round(current));
      if (current >= score) clearInterval(timer);
    }, 20);
    return () => clearInterval(timer);
  }, [score]);

  const color = score >= 80 ? '#10B981' : score >= 60 ? '#F59E0B' : '#EF4444';
  const dashArray = 188;
  const dashOffset = animated ? dashArray - (score / 100) * dashArray : dashArray;

  return (
    <div style={{ textAlign: 'center' }}>
      <svg width="140" height="80" viewBox="0 0 140 80">
        <path d="M 10 75 A 60 60 0 0 1 130 75" fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="10" strokeLinecap="round" />
        <path
          d="M 10 75 A 60 60 0 0 1 130 75"
          fill="none"
          stroke={color}
          strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={dashArray}
          strokeDashoffset={dashOffset}
          style={{ transition: 'stroke-dashoffset 1.2s cubic-bezier(0.4, 0, 0.2, 1)' }}
        />
        <circle cx="70" cy="75" r="5" fill={color} />
      </svg>
      <div style={{ fontSize: 28, fontWeight: 800, color, fontFamily: 'Outfit, sans-serif', marginTop: -8 }}>
        {displayScore}%
      </div>
      <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 4 }}>Sentiment Score</div>
    </div>
  );
};

export const AiInsightsPanel: React.FC<AiInsightsPanelProps> = ({ product }) => {
  const showAll = false;

  return (
    <div className="glass-card" style={{ borderRadius: 2, padding: 28, borderTop: '2px solid rgba(255,153,0,0.35)' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24 }}>
        <div style={{
          width: 44, height: 44,
          /* Sharp — 2px */
          borderRadius: 2,
          background: 'rgba(255,153,0,0.12)',
          border: '1px solid rgba(255,153,0,0.25)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <Brain size={22} color="#FF9900" />
        </div>
        <div>
          <h3 style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>AI Insights</h3>
          <p style={{ fontSize: 12, color: 'var(--text-secondary)', margin: 0 }}>Generated from {product.reviewCount.toLocaleString()} reviews</p>
        </div>
      </div>

      {/* AI Summary */}
      <div style={{
        background: 'rgba(255,153,0,0.04)',
        border: '1px solid rgba(255,153,0,0.12)',
        borderLeft: '3px solid #FF9900',
        /* Sharp — 0px */
        borderRadius: 2,
        padding: '14px 16px', marginBottom: 20,
      }}>
        <p style={{ fontSize: 13, color: 'var(--text-primary)', lineHeight: 1.7, margin: 0 }}>
          <span style={{ color: '#FF9900', fontWeight: 700 }}>AI Summary: </span>
          {product.description} Our analysis of {product.reviewCount.toLocaleString()} user reviews shows overwhelmingly positive sentiment, particularly around build quality and performance.
        </p>
      </div>

      {/* Sentiment Gauge */}
      <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 24 }}>
        <AnimatedGauge score={product.sentimentScore} />
      </div>

      {/* Recommendation Score */}
      <div style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <Zap size={14} color="#FF9900" />
            <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>AI Recommendation Score</span>
          </div>
          <span style={{ fontSize: 18, fontWeight: 800, color: '#FF9900', fontFamily: 'Outfit, sans-serif' }}>{product.aiScore}/100</span>
        </div>
        <div className="progress-bar">
          <motion.div
            className="progress-fill"
            initial={{ width: 0 }}
            animate={{ width: `${product.aiScore}%` }}
            transition={{ duration: 1.2, ease: 'easeOut', delay: 0.5 }}
          />
        </div>
      </div>

      {/* Pros */}
      <div style={{ marginBottom: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 10 }}>
          <ThumbsUp size={14} color="#10B981" />
          <span style={{ fontSize: 13, fontWeight: 700, color: '#10B981' }}>Pros</span>
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
          {(showAll ? product.pros : product.pros.slice(0, 3)).map((pro, i) => (
            <motion.span
              key={i}
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: i * 0.08 }}
              className="tag-pro"
            >
              <CheckCircle size={11} />
              {pro}
            </motion.span>
          ))}
        </div>
      </div>

      {/* Cons */}
      <div style={{ marginBottom: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 10 }}>
          <ThumbsDown size={14} color="#EF4444" />
          <span style={{ fontSize: 13, fontWeight: 700, color: '#EF4444' }}>Cons</span>
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
          {(showAll ? product.cons : product.cons.slice(0, 3)).map((con, i) => (
            <motion.span
              key={i}
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: i * 0.08 + 0.2 }}
              className="tag-con"
            >
              <XCircle size={11} />
              {con}
            </motion.span>
          ))}
        </div>
      </div>

      {/* Feature Scores */}
      <div style={{ marginTop: 20, paddingTop: 20, borderTop: '1px solid var(--border-color)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 12 }}>
          <BarChart2 size={14} color="#6366F1" />
          <span style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)' }}>Key Specifications</span>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {Object.entries(product.features).slice(0, 5).map(([key, value]) => (
            <div key={key} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: 12, color: 'var(--text-secondary)', fontWeight: 500 }}>{key}</span>
              <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-primary)' }}>{value}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
