import React, { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Mic, Sparkles, Clock, X, TrendingUp } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useStore } from '../../store/useStore';
import { AI_CHAT_SUGGESTIONS } from '../../data/mockData';

interface SearchBarProps {
  size?: 'hero' | 'normal';
  placeholder?: string;
}

export const SearchBar: React.FC<SearchBarProps> = ({
  size = 'normal',
  placeholder = 'Search anything...',
}) => {
  const navigate = useNavigate();
  const { searchQuery, setSearchQuery, searchHistory, addToSearchHistory } = useStore();
  const [isFocused, setIsFocused] = useState(false);
  const [localQuery, setLocalQuery] = useState(searchQuery);
  const [isListening, setIsListening] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const suggestions = AI_CHAT_SUGGESTIONS.filter((s) =>
    localQuery ? s.toLowerCase().includes(localQuery.toLowerCase()) : true
  ).slice(0, 5);

  const handleSearch = (q?: string) => {
    const query = q || localQuery;
    if (!query.trim()) return;
    addToSearchHistory(query);
    setSearchQuery(query);
    setLocalQuery(query);
    setIsFocused(false);
    navigate('/products');
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') handleSearch();
    if (e.key === 'Escape') setIsFocused(false);
  };

  const toggleVoice = () => {
    setIsListening(!isListening);
    setTimeout(() => setIsListening(false), 3000);
  };

  const isHero = size === 'hero';

  return (
    <div style={{ position: 'relative', width: '100%' }}>
      {/*
        AWS-inspired search bar:
        Sharp rectangular container, strong orange focus glow,
        professional enterprise appearance — NO rounded/pill shape
      */}
      <div
        className="search-ring"
        style={{
          display: 'flex',
          alignItems: 'center',
          padding: isHero ? '0' : '0',
          gap: 0,
          /* Sharp rectangle — search-ring uses border-radius: 3px from CSS */
          overflow: 'hidden',
        }}
      >
        {/* Left: Category selector (enterprise-style) */}
        <div style={{
          padding: isHero ? '14px 16px' : '11px 14px',
          borderRight: '1px solid rgba(255,255,255,0.1)',
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          flexShrink: 0,
          cursor: 'pointer',
        }}>
          <Search
            size={isHero ? 20 : 16}
            style={{ color: isFocused ? '#FF9900' : 'rgba(255,255,255,0.45)', transition: 'color 0.15s' }}
          />
        </div>

        <input
          ref={inputRef}
          type="text"
          value={localQuery}
          onChange={(e) => setLocalQuery(e.target.value)}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setTimeout(() => setIsFocused(false), 200)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          aria-label="Search products"
          style={{
            flex: 1,
            background: 'transparent',
            border: 'none',
            color: 'white',
            fontSize: isHero ? 17 : 14,
            fontFamily: 'Inter, sans-serif',
            fontWeight: 400,
            padding: isHero ? '14px 12px' : '11px 12px',
            outline: 'none',
          }}
        />

        {localQuery && (
          <motion.button
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            onClick={() => setLocalQuery('')}
            style={{
              padding: '6px 8px',
              background: 'none',
              border: 'none',
              color: 'rgba(255,255,255,0.35)',
              cursor: 'pointer',
              display: 'flex',
              borderRadius: 0,
            }}
          >
            <X size={13} />
          </motion.button>
        )}

        {/* Voice */}
        <motion.button
          whileTap={{ scale: 0.9 }}
          onClick={toggleVoice}
          style={{
            padding: isHero ? '14px 10px' : '11px 8px',
            background: 'none',
            border: 'none',
            borderLeft: '1px solid rgba(255,255,255,0.08)',
            color: isListening ? '#FF9900' : 'rgba(255,255,255,0.35)',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            borderRadius: 0,
            transition: 'color 0.15s',
          }}
          aria-label="Voice search"
        >
          <motion.div animate={isListening ? { scale: [1, 1.2, 1] } : {}} transition={{ repeat: Infinity, duration: 0.8 }}>
            <Mic size={16} />
          </motion.div>
        </motion.button>

        {/* AI Search Button — sharp rectangle, no pill */}
        <motion.button
          whileHover={{ scale: 1.0 }}
          whileTap={{ scale: 0.97 }}
          onClick={() => handleSearch()}
          style={{
            display: 'flex', alignItems: 'center', gap: 6,
            padding: isHero ? '14px 20px' : '11px 16px',
            background: '#FF9900',
            color: '#0D1117',
            border: 'none',
            /* SHARP — not a pill */
            borderRadius: 0,
            fontWeight: 700,
            fontSize: isHero ? 14 : 13,
            cursor: 'pointer',
            flexShrink: 0,
            fontFamily: 'Inter, sans-serif',
            transition: 'background 0.15s',
            letterSpacing: '0.01em',
          }}
          onMouseEnter={(e) => (e.currentTarget as HTMLElement).style.background = '#FFB84D'}
          onMouseLeave={(e) => (e.currentTarget as HTMLElement).style.background = '#FF9900'}
        >
          <Sparkles size={13} />
          {isHero ? 'AI Search' : 'Search'}
        </motion.button>
      </div>

      {/* Dropdown — sharp rectangular panel */}
      <AnimatePresence>
        {isFocused && (
          <motion.div
            initial={{ opacity: 0, y: -8, scale: 0.99 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -8, scale: 0.99 }}
            transition={{ duration: 0.12 }}
            style={{
              position: 'absolute',
              top: 'calc(100% + 4px)',
              left: 0,
              right: 0,
              zIndex: 999,
              background: 'rgba(13, 17, 23, 0.98)',
              border: '1px solid rgba(255,255,255,0.08)',
              borderTop: '2px solid #FF9900',
              /* Sharp dropdown — no border-radius */
              borderRadius: 0,
              padding: 16,
              boxShadow: '0 16px 48px rgba(0,0,0,0.5)',
            }}
          >
            {/* Suggestions */}
            {suggestions.length > 0 && (
              <div style={{ marginBottom: 16 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 8, paddingBottom: 8, borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                  <TrendingUp size={11} color="#FF9900" />
                  <span style={{ fontSize: 10, fontWeight: 700, color: '#FF9900', textTransform: 'uppercase', letterSpacing: '0.12em', fontFamily: 'JetBrains Mono, monospace' }}>
                    AI Suggestions
                  </span>
                </div>
                {suggestions.map((suggestion, i) => (
                  <motion.button
                    key={i}
                    whileHover={{ background: 'rgba(255,153,0,0.07)', x: 2 }}
                    onClick={() => handleSearch(suggestion)}
                    style={{
                      display: 'flex', alignItems: 'center', gap: 10,
                      width: '100%', padding: '8px 10px', border: 'none',
                      background: 'transparent',
                      /* Sharp row item — no border-radius */
                      borderRadius: 0,
                      cursor: 'pointer', textAlign: 'left',
                      color: 'rgba(255,255,255,0.75)', fontSize: 13,
                      transition: 'all 0.12s',
                      borderLeft: '2px solid transparent',
                    }}
                    onMouseEnter={(e) => (e.currentTarget as HTMLElement).style.borderLeftColor = '#FF9900'}
                    onMouseLeave={(e) => (e.currentTarget as HTMLElement).style.borderLeftColor = 'transparent'}
                  >
                    <Sparkles size={13} color="#FF9900" />
                    {suggestion}
                  </motion.button>
                ))}
              </div>
            )}

            {/* Recent Searches */}
            {searchHistory.length > 0 && (
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 8, paddingBottom: 8, borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                  <Clock size={11} color="#4B5563" />
                  <span style={{ fontSize: 10, fontWeight: 700, color: '#4B5563', textTransform: 'uppercase', letterSpacing: '0.12em', fontFamily: 'JetBrains Mono, monospace' }}>
                    Recent
                  </span>
                </div>
                {searchHistory.slice(0, 4).map((item, i) => (
                  <motion.button
                    key={i}
                    whileHover={{ background: 'rgba(255,255,255,0.04)', x: 2 }}
                    onClick={() => handleSearch(item)}
                    style={{
                      display: 'flex', alignItems: 'center', gap: 10,
                      width: '100%', padding: '7px 10px', border: 'none',
                      background: 'transparent', borderRadius: 0,
                      cursor: 'pointer', textAlign: 'left',
                      color: 'rgba(255,255,255,0.4)', fontSize: 13,
                      transition: 'all 0.12s',
                    }}
                  >
                    <Clock size={12} />
                    {item}
                  </motion.button>
                ))}
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
