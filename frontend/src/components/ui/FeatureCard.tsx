import React from 'react';
import { motion } from 'framer-motion';
import { LucideIcon } from 'lucide-react';

interface FeatureCardProps {
  icon: LucideIcon;
  title: string;
  description: string;
  color: string;
  index: number;
}

export const FeatureCard: React.FC<FeatureCardProps> = ({ icon: Icon, title, description, color, index }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 32 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ delay: index * 0.08, duration: 0.4 }}
      whileHover={{ y: -4 }}
      style={{ position: 'relative', cursor: 'default' }}
    >
      {/*
        Feature card — sharp rectangular panel.
        Enterprise precision: thin border, strong top accent line,
        no blob shapes or organic curves.
      */}
      <div
        style={{
          background: 'var(--bg-card)',
          border: '1px solid var(--border-color)',
          /* Top accent: 2px colored stripe signals category */
          borderTop: `2px solid ${color}`,
          /* SHARP — 2px max */
          borderRadius: 2,
          padding: '28px 24px',
          height: '100%',
          position: 'relative',
          overflow: 'hidden',
          transition: 'border-color 0.2s, box-shadow 0.2s',
          boxShadow: '0 1px 4px rgba(0,0,0,0.06)',
        }}
        onMouseEnter={(e) => {
          (e.currentTarget as HTMLElement).style.boxShadow = `0 6px 20px rgba(0,0,0,0.12)`;
          (e.currentTarget as HTMLElement).style.borderColor = `${color}50`;
        }}
        onMouseLeave={(e) => {
          (e.currentTarget as HTMLElement).style.boxShadow = '0 1px 4px rgba(0,0,0,0.06)';
          (e.currentTarget as HTMLElement).style.borderColor = 'var(--border-color)';
          (e.currentTarget as HTMLElement).style.borderTopColor = color;
        }}
      >
        {/* Subtle corner glow — stays in upper-right, contained */}
        <div style={{
          position: 'absolute', top: 0, right: 0,
          width: 80, height: 80,
          background: color,
          opacity: 0.04,
          filter: 'blur(24px)',
          transition: 'opacity 0.3s',
        }} />

        {/* Icon — sharp rectangular container, not circle */}
        <motion.div
          whileHover={{ rotate: 5, scale: 1.08 }}
          transition={{ type: 'spring', stiffness: 280 }}
          style={{
            width: 48, height: 48,
            /* Sharp — 2px */
            borderRadius: 2,
            background: `${color}12`,
            border: `1px solid ${color}28`,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            marginBottom: 18,
          }}
        >
          <Icon size={22} color={color} strokeWidth={1.8} />
        </motion.div>

        {/* Title */}
        <h3 style={{
          fontFamily: 'Outfit, sans-serif',
          fontSize: 16, fontWeight: 700,
          color: 'var(--text-primary)',
          marginBottom: 8,
          letterSpacing: '-0.01em',
        }}>
          {title}
        </h3>

        {/* Description */}
        <p style={{
          fontSize: 13, color: 'var(--text-secondary)',
          lineHeight: 1.65, margin: 0,
        }}>
          {description}
        </p>

        {/* Bottom data-line indicator — sharp horizontal bar */}
        <motion.div
          initial={{ width: 0 }}
          whileInView={{ width: 32 }}
          viewport={{ once: true }}
          transition={{ delay: index * 0.08 + 0.25, duration: 0.35 }}
          style={{
            height: 2,
            /* Sharp — no border-radius */
            borderRadius: 0,
            background: color,
            marginTop: 18,
          }}
        />
      </div>
    </motion.div>
  );
};
