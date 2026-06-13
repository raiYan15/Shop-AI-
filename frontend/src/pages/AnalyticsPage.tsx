import React from 'react';
import { motion } from 'framer-motion';
import {
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend,
} from 'recharts';
import { Users, Search, Target, Brain } from 'lucide-react';
import { Footer } from '../components/layout/Footer';
import { ANALYTICS_DATA } from '../data/mockData';

const METRICS = [
  { label: 'Total Searches', value: '2.4M', change: '+18.3%', icon: Search, color: '#FF9900' },
  { label: 'Active Users', value: '147K', change: '+12.1%', icon: Users, color: '#6366F1' },
  { label: 'Recommendations', value: '8.9M', change: '+24.7%', icon: Brain, color: '#10B981' },
  { label: 'AI Accuracy', value: '95.4%', change: '+2.1%', icon: Target, color: '#F59E0B' },
];

const CustomTooltip: React.FC<any> = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{
      background: 'rgba(13,17,23,0.98)',
      border: '1px solid rgba(255,255,255,0.07)',
      /* Sharp tooltip — 2px */
      borderRadius: 2,
      borderTop: '2px solid #FF9900',
      padding: '10px 14px',
    }}>
      <div style={{ fontSize: 10, color: 'rgba(255,255,255,0.4)', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.06em', fontFamily: 'JetBrains Mono, monospace' }}>{label}</div>
      {payload.map((entry: any, i: number) => (
        <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 3 }}>
          <div style={{ width: 8, height: 2, background: entry.color, borderRadius: 0 }} />
          <span style={{ fontSize: 12, color: 'rgba(255,255,255,0.7)', fontWeight: 500, fontFamily: 'JetBrains Mono, monospace' }}>{entry.name}: </span>
          <span style={{ fontSize: 12, color: 'white', fontWeight: 700, fontFamily: 'JetBrains Mono, monospace' }}>
            {typeof entry.value === 'number' ? entry.value.toLocaleString() : entry.value}
          </span>
        </div>
      ))}
    </div>
  );
};

/* Sharp chart container — no rounded corners, accent top border */
const chartStyle = {
  background: 'var(--bg-card)',
  borderRadius: 2,
  borderTop: '2px solid rgba(255,153,0,0.3)',
  border: '1px solid var(--border-color)',
  padding: '24px',
  boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
};

export const AnalyticsPage: React.FC = () => {
  return (
    <div className="page-wrapper">
      {/* Header */}
      <div style={{ background: 'linear-gradient(180deg, #0D1117, var(--bg-primary))', paddingBottom: 56 }}>
        <div className="container" style={{ paddingTop: 48 }}>
          <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}>
            <div className="section-label">Executive Dashboard</div>
            <h1 className="section-title" style={{ color: 'white' }}>
              Analytics &{' '}
              <span style={{ color: '#FF9900' }}>AI Performance</span>
            </h1>
            <p style={{ color: 'rgba(255,255,255,0.35)', marginTop: 10, fontSize: 14, fontFamily: 'JetBrains Mono, monospace' }}>
              Real-time insights into platform performance, user behavior, and AI model metrics
            </p>
          </motion.div>

          {/* Metric Cards — sharp rectangular data panels */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 12, marginTop: 36 }}>
            {METRICS.map(({ label, value, change, icon: Icon, color }, i) => (
              <motion.div
                key={label}
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.08 }}
                whileHover={{ y: -3 }}
                style={{
                  background: 'rgba(255,255,255,0.04)',
                  border: '1px solid rgba(255,255,255,0.06)',
                  borderLeft: `3px solid ${color}`,
                  /* Sharp rectangular metric card */
                  borderRadius: 2,
                  padding: '20px',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 14 }}>
                  <div style={{
                    width: 40, height: 40,
                    /* Sharp square icon container */
                    borderRadius: 2,
                    background: `${color}18`, display: 'flex', alignItems: 'center', justifyContent: 'center',
                  }}>
                    <Icon size={18} color={color} />
                  </div>
                  {/* Change badge — sharp */}
                  <span style={{
                    fontSize: 11, fontWeight: 700, color: '#10B981',
                    background: 'rgba(16,185,129,0.1)', padding: '2px 8px',
                    /* Sharp badge — 2px */
                    borderRadius: 2,
                    border: '1px solid rgba(16,185,129,0.2)',
                    fontFamily: 'JetBrains Mono, monospace',
                  }}>
                    {change}
                  </span>
                </div>
                <div style={{ fontSize: 30, fontWeight: 900, color: 'white', fontFamily: 'Outfit, sans-serif', letterSpacing: '-0.03em' }}>
                  {value}
                </div>
                <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.35)', marginTop: 3, textTransform: 'uppercase', letterSpacing: '0.06em', fontFamily: 'JetBrains Mono, monospace' }}>{label}</div>
              </motion.div>
            ))}
          </div>
        </div>
      </div>

      <div className="container" style={{ paddingBottom: 80 }}>
        {/* Search Trends Chart */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          style={{ ...chartStyle, marginBottom: 20 }}
        >
          <div style={{ marginBottom: 18 }}>
            <h3 style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 2 }}>Search & Recommendation Trends</h3>
            <p style={{ fontSize: 12, color: 'var(--text-secondary)', fontFamily: 'JetBrains Mono, monospace' }}>Monthly platform activity over the last 7 months</p>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={ANALYTICS_DATA.searchTrends}>
              <defs>
                <linearGradient id="searchGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#FF9900" stopOpacity={0.25} />
                  <stop offset="95%" stopColor="#FF9900" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="recGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#6366F1" stopOpacity={0.2} />
                  <stop offset="95%" stopColor="#6366F1" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
              <XAxis dataKey="month" tick={{ fontSize: 11, fill: 'var(--text-secondary)', fontFamily: 'JetBrains Mono, monospace' }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 11, fill: 'var(--text-secondary)', fontFamily: 'JetBrains Mono, monospace' }} axisLine={false} tickLine={false} />
              <Tooltip content={<CustomTooltip />} />
              <Legend wrapperStyle={{ fontSize: 12, color: 'var(--text-secondary)', fontFamily: 'JetBrains Mono, monospace' }} />
              <Area type="monotone" dataKey="searches" stroke="#FF9900" strokeWidth={2} fill="url(#searchGrad)" name="Searches" />
              <Area type="monotone" dataKey="recommendations" stroke="#6366F1" strokeWidth={2} fill="url(#recGrad)" name="Recommendations" />
            </AreaChart>
          </ResponsiveContainer>
        </motion.div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(380px, 1fr))', gap: 20, marginBottom: 20 }}>
          {/* Category Pie */}
          <motion.div
            initial={{ opacity: 0, x: -16 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            style={chartStyle}
          >
            <div style={{ marginBottom: 18 }}>
              <h3 style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 2 }}>Category Popularity</h3>
              <p style={{ fontSize: 12, color: 'var(--text-secondary)', fontFamily: 'JetBrains Mono, monospace' }}>Distribution of user interest by category</p>
            </div>
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie
                  data={ANALYTICS_DATA.categoryPopularity}
                  cx="50%" cy="50%"
                  innerRadius={65} outerRadius={105}
                  paddingAngle={2}
                  dataKey="value"
                >
                  {ANALYTICS_DATA.categoryPopularity.map((entry, i) => (
                    <Cell key={i} fill={entry.fill} strokeWidth={0} />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
                <Legend wrapperStyle={{ fontSize: 11, fontFamily: 'JetBrains Mono, monospace' }} />
              </PieChart>
            </ResponsiveContainer>
          </motion.div>

          {/* User Interests Bar */}
          <motion.div
            initial={{ opacity: 0, x: 16 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            style={chartStyle}
          >
            <div style={{ marginBottom: 18 }}>
              <h3 style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 2 }}>User Interests Profile</h3>
              <p style={{ fontSize: 12, color: 'var(--text-secondary)', fontFamily: 'JetBrains Mono, monospace' }}>Interest scores by lifestyle segment</p>
            </div>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={ANALYTICS_DATA.userInterests} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 10, fill: 'var(--text-secondary)', fontFamily: 'JetBrains Mono, monospace' }} axisLine={false} tickLine={false} />
                <YAxis dataKey="interest" type="category" tick={{ fontSize: 11, fill: 'var(--text-secondary)', fontFamily: 'JetBrains Mono, monospace' }} axisLine={false} tickLine={false} width={80} />
                <Tooltip content={<CustomTooltip />} />
                {/* Sharp bars — radius 0 */}
                <Bar dataKey="score" radius={[0, 0, 0, 0]} name="Score">
                  {ANALYTICS_DATA.userInterests.map((_, i) => (
                    <Cell key={i} fill={`hsl(${35 + i * 15}, 88%, ${50 + i * 5}%)`} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </motion.div>
        </div>

        {/* AI Performance */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          style={chartStyle}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 18, flexWrap: 'wrap', gap: 10 }}>
            <div>
              <h3 style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 2 }}>AI Model Performance</h3>
              <p style={{ fontSize: 12, color: 'var(--text-secondary)', fontFamily: 'JetBrains Mono, monospace' }}>Recommendation accuracy & user satisfaction over 6 weeks</p>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <div style={{ width: 6, height: 6, borderRadius: '50%', background: '#10B981' }} />
              <span style={{ fontSize: 11, color: '#10B981', fontWeight: 600, fontFamily: 'JetBrains Mono, monospace' }}>Model v3.2 — Live</span>
            </div>
          </div>
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={ANALYTICS_DATA.performanceMetrics}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
              <XAxis dataKey="week" tick={{ fontSize: 11, fill: 'var(--text-secondary)', fontFamily: 'JetBrains Mono, monospace' }} axisLine={false} tickLine={false} />
              <YAxis domain={[70, 100]} tick={{ fontSize: 11, fill: 'var(--text-secondary)', fontFamily: 'JetBrains Mono, monospace' }} axisLine={false} tickLine={false} />
              <Tooltip content={<CustomTooltip />} />
              <Legend wrapperStyle={{ fontSize: 12, fontFamily: 'JetBrains Mono, monospace' }} />
              <Line type="monotone" dataKey="accuracy" stroke="#FF9900" strokeWidth={2} dot={{ fill: '#FF9900', r: 3, strokeWidth: 0 }} name="AI Accuracy %" />
              <Line type="monotone" dataKey="satisfaction" stroke="#10B981" strokeWidth={2} dot={{ fill: '#10B981', r: 3, strokeWidth: 0 }} name="User Satisfaction %" />
            </LineChart>
          </ResponsiveContainer>
        </motion.div>
      </div>
      <Footer />
    </div>
  );
};
