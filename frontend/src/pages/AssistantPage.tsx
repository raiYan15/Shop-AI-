import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MessageSquare, Package, Heart, Sparkles, Clock, Plus } from 'lucide-react';
import { ChatInterface } from '../components/ai/ChatInterface';
import { MOCK_PRODUCTS, AI_CHAT_SUGGESTIONS } from '../data/mockData';
import { useStore } from '../store/useStore';
import { Link } from 'react-router-dom';

interface Chat {
  id: string;
  title: string;
  timestamp: string;
}

const SAMPLE_CHATS: Chat[] = [
  { id: '1', title: 'Best gaming laptop under ₹70K', timestamp: '2 hours ago' },
  { id: '2', title: 'Noise canceling headphones comparison', timestamp: 'Yesterday' },
  { id: '3', title: 'Running shoes recommendations', timestamp: '2 days ago' },
  { id: '4', title: 'Best 4K TV under ₹1 lakh', timestamp: '3 days ago' },
];

export const AssistantPage: React.FC = () => {
  const { wishlist } = useStore();
  const [activeChat, setActiveChat] = useState('new');
  const [sidebarOpen, setSidebarOpen] = useState(true);

  return (
    <div className="page-wrapper" style={{ height: '100vh', overflow: 'hidden' }}>
      <div style={{ display: 'flex', height: 'calc(100vh - 72px)' }}>
        {/* LEFT SIDEBAR — sharp rectangular panel */}
        <AnimatePresence>
          {sidebarOpen && (
            <motion.aside
              initial={{ width: 0, opacity: 0 }}
              animate={{ width: 272, opacity: 1 }}
              exit={{ width: 0, opacity: 0 }}
              transition={{ duration: 0.25 }}
              style={{
                borderRight: '1px solid var(--border-color)',
                background: 'var(--bg-surface)',
                display: 'flex',
                flexDirection: 'column',
                overflow: 'hidden',
                flexShrink: 0,
                /* Sidebar: border-radius: 0 (per spec) */
                borderRadius: 0,
              }}
            >
              <div style={{ padding: '18px 14px', flex: 1, overflowY: 'auto' }}>
                {/* Header */}
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16, paddingBottom: 14, borderBottom: '1px solid var(--border-color)' }}>
                  <div>
                    <h2 style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)', margin: 0, textTransform: 'uppercase', letterSpacing: '0.06em' }}>AI Assistant</h2>
                    <p style={{ fontSize: 10, color: 'var(--text-secondary)', margin: 0, marginTop: 2, fontFamily: 'JetBrains Mono, monospace' }}>Powered by ShopMind AI</p>
                  </div>
                  <motion.button
                    whileHover={{ scale: 1.04 }}
                    onClick={() => setActiveChat('new')}
                    style={{
                      width: 28, height: 28,
                      /* Sharp square button */
                      borderRadius: 2,
                      background: '#FF9900',
                      border: 'none', cursor: 'pointer',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                    }}
                  >
                    <Plus size={13} color="#0D1117" />
                  </motion.button>
                </div>

                {/* New Chat Button — sharp */}
                <motion.button
                  whileHover={{ scale: 1.01 }}
                  whileTap={{ scale: 0.99 }}
                  onClick={() => setActiveChat('new')}
                  style={{
                    width: '100%', padding: '9px 12px',
                    background: activeChat === 'new' ? 'rgba(255,153,0,0.08)' : 'transparent',
                    border: `1px solid ${activeChat === 'new' ? 'rgba(255,153,0,0.25)' : 'var(--border-color)'}`,
                    borderLeft: activeChat === 'new' ? '3px solid #FF9900' : '3px solid transparent',
                    /* Sharp */
                    borderRadius: 2,
                    cursor: 'pointer',
                    display: 'flex', alignItems: 'center', gap: 7,
                    color: activeChat === 'new' ? '#FF9900' : 'var(--text-secondary)',
                    fontSize: 12, fontWeight: 700,
                    marginBottom: 14,
                    textTransform: 'uppercase',
                    letterSpacing: '0.04em',
                  }}
                >
                  <Sparkles size={12} />
                  New Conversation
                </motion.button>

                {/* Recent Chats */}
                <div style={{ marginBottom: 20 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 5, marginBottom: 8 }}>
                    <Clock size={10} color="var(--text-secondary)" />
                    <span style={{ fontSize: 10, fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.08em', fontFamily: 'JetBrains Mono, monospace' }}>
                      Recent Chats
                    </span>
                  </div>
                  {SAMPLE_CHATS.map((chat) => (
                    <motion.button
                      key={chat.id}
                      whileHover={{ x: 2 }}
                      onClick={() => setActiveChat(chat.id)}
                      style={{
                        width: '100%', padding: '9px 10px',
                        background: activeChat === chat.id ? 'rgba(255,153,0,0.06)' : 'transparent',
                        border: 'none',
                        /* Sharp row item */
                        borderRadius: 0,
                        borderLeft: `2px solid ${activeChat === chat.id ? '#FF9900' : 'transparent'}`,
                        cursor: 'pointer', textAlign: 'left',
                        marginBottom: 1,
                        transition: 'all 0.12s',
                      }}
                    >
                      <div style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-primary)', lineHeight: 1.35, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {chat.title}
                      </div>
                      <div style={{ fontSize: 10, color: 'var(--text-secondary)', marginTop: 2, fontFamily: 'JetBrains Mono, monospace' }}>{chat.timestamp}</div>
                    </motion.button>
                  ))}
                </div>

                {/* Saved Products */}
                {wishlist.length > 0 && (
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 5, marginBottom: 8 }}>
                      <Heart size={10} color="#EF4444" />
                      <span style={{ fontSize: 10, fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.08em', fontFamily: 'JetBrains Mono, monospace' }}>
                        Saved ({wishlist.length})
                      </span>
                    </div>
                    {wishlist.slice(0, 3).map((product) => (
                      <Link
                        key={product.id}
                        to={`/products/${product.id}`}
                        style={{
                          display: 'flex', alignItems: 'center', gap: 8,
                          padding: '7px 8px',
                          /* Sharp item card */
                          borderRadius: 2,
                          textDecoration: 'none', marginBottom: 3,
                          background: 'rgba(255,255,255,0.02)',
                          border: '1px solid var(--border-color)',
                          transition: 'border-color 0.12s',
                        }}
                        onMouseEnter={(e) => (e.currentTarget as HTMLElement).style.borderColor = 'rgba(255,153,0,0.25)'}
                        onMouseLeave={(e) => (e.currentTarget as HTMLElement).style.borderColor = 'var(--border-color)'}
                      >
                        <img src={product.image} alt={product.name} style={{ width: 32, height: 32, borderRadius: 2, objectFit: 'cover', flexShrink: 0 }} />
                        <div style={{ flex: 1, minWidth: 0 }}>
                          <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                            {product.name}
                          </div>
                          <div style={{ fontSize: 11, color: '#FF9900', fontWeight: 700, fontFamily: 'JetBrains Mono, monospace' }}>
                            ₹{product.price.toLocaleString('en-IN')}
                          </div>
                        </div>
                      </Link>
                    ))}
                  </div>
                )}

                {/* Suggestions */}
                <div style={{ marginTop: 20 }}>
                  <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 8, fontFamily: 'JetBrains Mono, monospace' }}>
                    Try asking...
                  </div>
                  {AI_CHAT_SUGGESTIONS.slice(0, 4).map((s, i) => (
                    <div key={i} style={{
                      fontSize: 11, color: 'var(--text-secondary)', padding: '6px 9px',
                      /* Sharp suggestion chip */
                      borderRadius: 2,
                      marginBottom: 3,
                      background: 'rgba(255,153,0,0.03)',
                      border: '1px solid rgba(255,153,0,0.07)',
                      cursor: 'pointer',
                      transition: 'border-color 0.12s, background 0.12s',
                    }}
                      onMouseEnter={(e) => {
                        (e.currentTarget as HTMLElement).style.background = 'rgba(255,153,0,0.07)';
                        (e.currentTarget as HTMLElement).style.borderColor = 'rgba(255,153,0,0.18)';
                      }}
                      onMouseLeave={(e) => {
                        (e.currentTarget as HTMLElement).style.background = 'rgba(255,153,0,0.03)';
                        (e.currentTarget as HTMLElement).style.borderColor = 'rgba(255,153,0,0.07)';
                      }}
                    >
                      💡 {s}
                    </div>
                  ))}
                </div>
              </div>
            </motion.aside>
          )}
        </AnimatePresence>

        {/* CENTER: Chat */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', position: 'relative' }}>
          {/* Chat Header — sharp bar */}
          <div style={{
            padding: '14px 20px',
            borderBottom: '2px solid rgba(255,153,0,0.15)',
            display: 'flex', alignItems: 'center', gap: 10,
            background: 'var(--bg-surface)',
            borderRadius: 0,
          }}>
            <motion.button
              whileHover={{ scale: 1.04 }}
              onClick={() => setSidebarOpen(!sidebarOpen)}
              style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-secondary)', display: 'flex', padding: 4, borderRadius: 2 }}
            >
              <MessageSquare size={16} />
            </motion.button>
            <div style={{ width: 7, height: 7, borderRadius: '50%', background: '#10B981' }} />
            <span style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>ShopMind AI</span>
            <span style={{ fontSize: 11, color: '#10B981', fontFamily: 'JetBrains Mono, monospace' }}>Online</span>
            <div style={{ marginLeft: 'auto', display: 'flex', gap: 6 }}>
              {/* Sharp status chip — not pill */}
              <span style={{
                fontSize: 10, padding: '3px 9px',
                borderRadius: 2,
                background: 'rgba(255,153,0,0.08)', color: '#FF9900',
                border: '1px solid rgba(255,153,0,0.18)', fontWeight: 700,
                textTransform: 'uppercase', letterSpacing: '0.06em',
                fontFamily: 'JetBrains Mono, monospace',
              }}>
                AI Powered
              </span>
            </div>
          </div>

          {/* Chat Interface */}
          <div style={{ flex: 1, overflow: 'hidden' }}>
            <ChatInterface />
          </div>
        </div>

        {/* RIGHT: Product Recommendations Sidebar — sharp panel */}
        <aside style={{
          width: 288,
          borderLeft: '1px solid var(--border-color)',
          background: 'var(--bg-surface)',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          /* Sidebar: radius 0 per spec */
          borderRadius: 0,
        }}
          className="right-sidebar"
        >
          <div style={{ padding: '16px 14px', borderBottom: '2px solid rgba(255,153,0,0.15)' }}>
            <h3 style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-primary)', margin: 0, textTransform: 'uppercase', letterSpacing: '0.08em' }}>Live Recommendations</h3>
            <p style={{ fontSize: 10, color: 'var(--text-secondary)', margin: '3px 0 0', fontFamily: 'JetBrains Mono, monospace' }}>AI-curated for your session</p>
          </div>
          <div style={{ flex: 1, overflowY: 'auto', padding: '10px' }}>
            {MOCK_PRODUCTS.slice(0, 5).map((product, i) => (
              <motion.div
                key={product.id}
                initial={{ opacity: 0, x: 16 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.08 }}
              >
                <Link
                  to={`/products/${product.id}`}
                  style={{
                    display: 'flex', gap: 9, padding: '9px',
                    marginBottom: 6,
                    /* Sharp item card — 2px */
                    borderRadius: 2,
                    textDecoration: 'none',
                    border: '1px solid var(--border-color)',
                    background: 'var(--bg-card)',
                    transition: 'all 0.15s',
                  }}
                  onMouseEnter={(e) => {
                    (e.currentTarget as HTMLElement).style.borderColor = 'rgba(255,153,0,0.3)';
                    (e.currentTarget as HTMLElement).style.background = 'rgba(255,153,0,0.03)';
                  }}
                  onMouseLeave={(e) => {
                    (e.currentTarget as HTMLElement).style.borderColor = 'var(--border-color)';
                    (e.currentTarget as HTMLElement).style.background = 'var(--bg-card)';
                  }}
                >
                  <img src={product.image} alt={product.name} style={{ width: 48, height: 48, borderRadius: 2, objectFit: 'cover', flexShrink: 0 }} />
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', marginBottom: 3 }}>
                      {product.name}
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 5, justifyContent: 'space-between' }}>
                      <span style={{ fontSize: 12, fontWeight: 800, color: '#FF9900', fontFamily: 'Outfit, sans-serif' }}>₹{product.price.toLocaleString('en-IN')}</span>
                      <span style={{ fontSize: 9, fontWeight: 700, color: '#10B981', background: 'rgba(16,185,129,0.08)', padding: '1px 5px', borderRadius: 2, fontFamily: 'JetBrains Mono, monospace' }}>
                        AI: {product.aiScore}
                      </span>
                    </div>
                  </div>
                </Link>
              </motion.div>
            ))}
          </div>
          <div style={{ padding: '10px', borderTop: '1px solid var(--border-color)' }}>
            <Link to="/products" className="btn-secondary" style={{ display: 'flex', justifyContent: 'center', fontSize: 12, gap: 6, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              <Package size={13} />
              Browse All
            </Link>
          </div>
        </aside>
      </div>

      <style>{`
        @media (max-width: 1024px) { .right-sidebar { display: none !important; } }
        @media (max-width: 640px) { aside:first-child { display: none !important; } }
      `}</style>
    </div>
  );
};
