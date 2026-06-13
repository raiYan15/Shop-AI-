import React from 'react';
import { Link } from 'react-router-dom';
import { Brain, X, Globe, Code2, Sparkles, Mail } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer style={{
      background: '#0D1117',
      borderTop: '1px solid rgba(255,255,255,0.06)',
      borderRadius: 0,
      padding: '56px 0 28px',
    }}>
      <div className="container">
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 40, marginBottom: 48 }}>
          {/* Brand */}
          <div>
            <Link to="/" style={{ textDecoration: 'none', display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
              <div style={{
                width: 32, height: 32,
                /* Sharp — 2px */
                borderRadius: 2,
                background: '#FF9900',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}>
                <Brain size={16} color="#0D1117" />
              </div>
              <span style={{ fontFamily: 'Outfit, sans-serif', fontWeight: 800, fontSize: 17, color: 'white' }}>
                ShopMind <span style={{ color: '#FF9900' }}>AI</span>
              </span>
            </Link>
            <p style={{ color: '#4B5563', fontSize: 13, lineHeight: 1.7, marginBottom: 20, maxWidth: 240 }}>
              The future of shopping is here. AI-powered recommendations, semantic search, and intelligent insights.
            </p>
            {/* Social icons — sharp rectangles */}
            <div style={{ display: 'flex', gap: 8 }}>
              {[X, Globe, Code2].map((Icon, i) => (
                <a key={i} href="#" style={{
                  width: 32, height: 32,
                  /* Sharp rectangle — not circle */
                  borderRadius: 2,
                  background: 'rgba(255,255,255,0.05)',
                  border: '1px solid rgba(255,255,255,0.08)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  color: '#4B5563', textDecoration: 'none',
                  transition: 'all 0.15s',
                }}
                  onMouseEnter={(e) => {
                    (e.currentTarget as HTMLElement).style.background = 'rgba(255,153,0,0.12)';
                    (e.currentTarget as HTMLElement).style.color = '#FF9900';
                    (e.currentTarget as HTMLElement).style.borderColor = 'rgba(255,153,0,0.25)';
                  }}
                  onMouseLeave={(e) => {
                    (e.currentTarget as HTMLElement).style.background = 'rgba(255,255,255,0.05)';
                    (e.currentTarget as HTMLElement).style.color = '#4B5563';
                    (e.currentTarget as HTMLElement).style.borderColor = 'rgba(255,255,255,0.08)';
                  }}
                >
                  <Icon size={14} />
                </a>
              ))}
            </div>
          </div>

          {/* Links */}
          {[
            { title: 'Platform', links: ['Home', 'Products', 'Recommendations', 'AI Assistant', 'Analytics'] },
            { title: 'Company', links: ['About Us', 'Careers', 'Press', 'Blog', 'Partners'] },
            { title: 'Support', links: ['Help Center', 'Contact Us', 'Privacy Policy', 'Terms of Service', 'Cookie Settings'] },
          ].map(({ title, links }) => (
            <div key={title}>
              <h4 style={{ color: '#F0F6FC', fontWeight: 700, fontSize: 11, marginBottom: 16, letterSpacing: '0.1em', textTransform: 'uppercase', fontFamily: 'JetBrains Mono, monospace' }}>
                {title}
              </h4>
              <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 10 }}>
                {links.map((link) => (
                  <li key={link}>
                    <a href="#" style={{
                      color: '#4B5563', textDecoration: 'none', fontSize: 13,
                      transition: 'color 0.15s',
                    }}
                      onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.color = '#FF9900'; }}
                      onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.color = '#4B5563'; }}
                    >
                      {link}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}

          {/* Newsletter — sharp rectangular input */}
          <div>
            <h4 style={{ color: '#F0F6FC', fontWeight: 700, fontSize: 11, marginBottom: 16, letterSpacing: '0.1em', textTransform: 'uppercase', fontFamily: 'JetBrains Mono, monospace' }}>
              Stay Updated
            </h4>
            <p style={{ color: '#4B5563', fontSize: 13, marginBottom: 14, lineHeight: 1.6 }}>
              Get AI-powered deals and product insights in your inbox.
            </p>
            <div style={{ display: 'flex', gap: 0 }}>
              <input
                type="email"
                placeholder="your@email.com"
                style={{
                  flex: 1, padding: '9px 12px',
                  /* Sharp rectangular input */
                  borderRadius: 0,
                  background: 'rgba(255,255,255,0.05)',
                  border: '1px solid rgba(255,255,255,0.09)',
                  borderRight: 'none',
                  color: 'white', fontSize: 13,
                  outline: 'none',
                  fontFamily: 'Inter, sans-serif',
                }}
                onFocus={(e) => {
                  (e.currentTarget as HTMLElement).style.borderColor = 'rgba(255,153,0,0.4)';
                }}
                onBlur={(e) => {
                  (e.currentTarget as HTMLElement).style.borderColor = 'rgba(255,255,255,0.09)';
                }}
              />
              <button style={{
                padding: '9px 14px',
                /* Sharp rectangle — not rounded */
                borderRadius: 0,
                background: '#FF9900',
                border: 'none',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                color: '#0D1117',
                transition: 'background 0.15s',
              }}
                onMouseEnter={(e) => (e.currentTarget as HTMLElement).style.background = '#FFB84D'}
                onMouseLeave={(e) => (e.currentTarget as HTMLElement).style.background = '#FF9900'}
              >
                <Mail size={14} />
              </button>
            </div>
          </div>
        </div>

        {/* Bottom bar — sharp divider */}
        <div style={{
          borderTop: '1px solid rgba(255,255,255,0.05)',
          paddingTop: 22,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: 12,
        }}>
          <p style={{ color: '#374151', fontSize: 12, fontFamily: 'JetBrains Mono, monospace' }}>
            © 2026 ShopMind AI. All rights reserved. Built with <Sparkles style={{ display: 'inline', color: '#FF9900' }} size={11} /> AI.
          </p>
          <div style={{ display: 'flex', gap: 20 }}>
            {['Privacy', 'Terms', 'Cookies'].map((item) => (
              <a key={item} href="#" style={{ color: '#374151', textDecoration: 'none', fontSize: 12, fontFamily: 'JetBrains Mono, monospace' }}>
                {item}
              </a>
            ))}
          </div>
        </div>
      </div>
    </footer>
  );
};
