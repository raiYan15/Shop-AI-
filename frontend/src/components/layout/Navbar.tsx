import React, { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Brain,
  ShoppingCart,
  Heart,
  Bell,
  Moon,
  Sun,
  Menu,
  X,
  Sparkles,
  BarChart3,
  Home,
  Package,
  Star,
  MessageSquare,
  User,
  Activity,
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { useStore } from '../../store/useStore';
import { useBackendStatus } from '../../hooks/useBackendStatus';
import { getDashboard, signOut } from '../../services/api';

const NAV_LINKS_PUBLIC = [
  { path: '/', label: 'Home', icon: Home },
  { path: '/products', label: 'Products', icon: Package },
  { path: '/recommendations', label: 'Recommendations', icon: Star },
  { path: '/assistant', label: 'AI Assistant', icon: MessageSquare },
  { path: '/analytics', label: 'Analytics', icon: BarChart3 },
];

const NAV_LINKS_AUTH = [
  ...NAV_LINKS_PUBLIC,
  { path: '/profile', label: 'Dashboard', icon: User },
];

export const Navbar: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { darkMode, toggleDarkMode, currentUser, setCurrentUser } = useStore();
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const backend = useBackendStatus(30000);
  const isLoggedIn = currentUser !== null;
  const navLinks = isLoggedIn ? NAV_LINKS_AUTH : NAV_LINKS_PUBLIC;

  const { data: dashboard } = useQuery({
    queryKey: ['navbar-dashboard-summary'],
    queryFn: getDashboard,
    enabled: isLoggedIn,
    refetchInterval: 15000,
    staleTime: 10000,
  });

  const wishlistCount = dashboard?.metrics?.wishlist_count ?? 0;
  const cartCount = dashboard?.metrics?.cart_count ?? 0;

  const handleSignOut = async () => {
    await signOut();
    setCurrentUser(null);
    navigate('/signin');
  };

  const statusColor = backend.status === 'online' && backend.modelsLoaded
    ? '#10B981'
    : backend.status === 'online'
    ? '#F59E0B'
    : backend.status === 'loading'
    ? '#6366F1'
    : '#EF4444';
  const statusLabel = backend.status === 'online' && backend.modelsLoaded
    ? 'AI Online'
    : backend.status === 'online'
    ? 'Loading...'
    : backend.status === 'loading'
    ? 'Connecting'
    : 'AI Offline';

  useEffect(() => {
    const handler = () => setScrolled(window.scrollY > 20);
    window.addEventListener('scroll', handler, { passive: true });
    return () => window.removeEventListener('scroll', handler);
  }, []);

  return (
    <>
      <motion.nav
        initial={{ y: -100 }}
        animate={{ y: 0 }}
        transition={{ duration: 0.4, ease: 'easeOut' }}
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          zIndex: 1000,
          height: 72,
          display: 'flex',
          alignItems: 'center',
          backdropFilter: scrolled ? 'blur(16px)' : 'none',
          WebkitBackdropFilter: scrolled ? 'blur(16px)' : 'none',
          background: scrolled
            ? darkMode
              ? 'rgba(13, 17, 23, 0.96)'
              : 'rgba(255, 255, 255, 0.96)'
            : 'transparent',
          borderBottom: scrolled
            ? `1px solid ${darkMode ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.08)'}`
            : '1px solid transparent',
          transition: 'all 0.25s cubic-bezier(0.4, 0, 0.2, 1)',
          /* No border-radius — navbar is rectangular */
          borderRadius: 0,
        }}
      >
        <div className="container" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
          {/* Logo — sharp square icon */}
          <Link to="/" style={{ textDecoration: 'none', display: 'flex', alignItems: 'center', gap: 10 }}>
            <motion.div
              whileHover={{ scale: 1.06 }}
              transition={{ type: 'spring', stiffness: 300 }}
              style={{
                width: 36,
                height: 36,
                background: '#FF9900',
                /* Sharp rectangle — no border-radius */
                borderRadius: 2,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 2px 8px rgba(255,153,0,0.35)',
                flexShrink: 0,
              }}
            >
              <Brain size={18} color="#0D1117" strokeWidth={2.5} />
            </motion.div>
            <div>
              <span style={{
                fontFamily: 'Outfit, sans-serif',
                fontWeight: 800,
                fontSize: 19,
                letterSpacing: '-0.03em',
                color: 'var(--text-primary)',
              }}>
                ShopMind
              </span>
              <span style={{
                fontFamily: 'Outfit, sans-serif',
                fontWeight: 800,
                fontSize: 19,
                letterSpacing: '-0.03em',
                color: '#FF9900',
              }}> AI</span>
            </div>
          </Link>

          {/* Desktop Nav — sharp links */}
          <nav style={{ display: 'flex', alignItems: 'center', gap: 2 }} className="desktop-nav">
            {navLinks.map(({ path, label, icon: Icon }) => (
              <Link
                key={path}
                to={path}
                className={`nav-link ${location.pathname === path ? 'active' : ''}`}
              >
                <Icon size={13} />
                {label}
              </Link>
            ))}
          </nav>

          {/* Right Actions */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            {/* Backend Status Indicator — sharp rectangular chip */}
            <div
              title={`Backend: ${statusLabel}${backend.totalProducts ? ` | ${backend.totalProducts.toLocaleString()} products` : ''}`}
              style={{
                display: 'flex', alignItems: 'center', gap: 5,
                padding: '4px 10px',
                /* Sharp rectangle — no pill shape */
                borderRadius: 2,
                background: `${statusColor}14`,
                border: `1px solid ${statusColor}28`,
                fontFamily: 'JetBrains Mono, monospace',
              }}
              className="status-badge"
            >
              <span style={{
                width: 6, height: 6, borderRadius: '50%',
                background: statusColor,
                boxShadow: backend.status === 'online' ? `0 0 5px ${statusColor}` : 'none',
                animation: backend.status === 'online' && backend.modelsLoaded ? 'pulse-glow 2s infinite' : 'none',
              }} />
              <Activity size={10} color={statusColor} />
              <span style={{ fontSize: 11, fontWeight: 600, color: statusColor }}>{statusLabel}</span>
            </div>

            {/* Dark Mode Toggle — sharp */}
            <motion.button
              whileHover={{ scale: 1.06 }}
              whileTap={{ scale: 0.92 }}
              onClick={toggleDarkMode}
              className="btn-ghost"
              style={{ padding: '7px', borderRadius: 2 }}
              aria-label="Toggle dark mode"
            >
              <AnimatePresence mode="wait">
                {darkMode ? (
                  <motion.div key="sun" initial={{ rotate: -90, opacity: 0 }} animate={{ rotate: 0, opacity: 1 }} exit={{ rotate: 90, opacity: 0 }} transition={{ duration: 0.18 }}>
                    <Sun size={17} color="#FF9900" />
                  </motion.div>
                ) : (
                  <motion.div key="moon" initial={{ rotate: 90, opacity: 0 }} animate={{ rotate: 0, opacity: 1 }} exit={{ rotate: -90, opacity: 0 }} transition={{ duration: 0.18 }}>
                    <Moon size={17} />
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.button>

            {/* Wishlist — sharp button */}
            {isLoggedIn && (
              <>
                <motion.button
                  whileHover={{ scale: 1.06 }}
                  whileTap={{ scale: 0.92 }}
                  className="btn-ghost"
                  style={{ padding: '7px', borderRadius: 2, position: 'relative' }}
                  aria-label="Notifications"
                >
                  <Bell size={17} />
                </motion.button>

                <motion.button
                  whileHover={{ scale: 1.06 }}
                  whileTap={{ scale: 0.92 }}
                  onClick={() => navigate('/profile')}
                  className="btn-ghost"
                  style={{ padding: '7px', borderRadius: 2, position: 'relative' }}
                  aria-label="Wishlist"
                >
                  <Heart size={17} />
                  {wishlistCount > 0 && (
                    <span style={{
                      position: 'absolute', top: 1, right: 1,
                      width: 15, height: 15,
                      borderRadius: 2,
                      background: '#EF4444', color: 'white',
                      fontSize: 9, fontWeight: 700,
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      fontFamily: 'JetBrains Mono, monospace',
                    }}>
                      {wishlistCount}
                    </span>
                  )}
                </motion.button>
              </>
            )}

            {/* Cart — sharp button */}
            <motion.button
              whileHover={{ scale: 1.06 }}
              whileTap={{ scale: 0.92 }}
              className="btn-ghost"
              style={{ padding: '7px', borderRadius: 2, position: 'relative' }}
              aria-label="Cart"
            >
              <ShoppingCart size={17} />
              {isLoggedIn && cartCount > 0 && (
                <span style={{
                  position: 'absolute', top: 1, right: 1,
                  width: 15, height: 15,
                  borderRadius: 2,
                  background: '#FF9900', color: '#0D1117',
                  fontSize: 9, fontWeight: 700,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontFamily: 'JetBrains Mono, monospace',
                }}>
                  {cartCount}
                </span>
              )}
            </motion.button>

            {/* Auth Buttons — conditional on login state */}
            {isLoggedIn ? (
              <>
                <Link to="/profile" style={{ display: 'flex', alignItems: 'center', gap: 7, textDecoration: 'none' }}>
                  <div style={{
                    width: 30, height: 30, borderRadius: 2,
                    background: '#FF9900',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontWeight: 700, fontSize: 13, color: '#0D1117',
                    fontFamily: 'Outfit, sans-serif',
                  }}>
                    {currentUser.first_name.charAt(0).toUpperCase()}
                  </div>
                  <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>
                    {currentUser.first_name}
                  </span>
                </Link>
                <motion.button
                  whileTap={{ scale: 0.95 }}
                  onClick={handleSignOut}
                  className="btn-ghost"
                  style={{ fontSize: 13, padding: '7px 12px', borderRadius: 2, color: '#EF4444' }}
                >
                  Sign Out
                </motion.button>
              </>
            ) : (
              <>
                {/* Sign In */}
                <Link to="/signin" className="btn-ghost" style={{ fontSize: 13 }}>Sign In</Link>

                {/* Get Started */}
                <Link to="/signup" className="btn-primary" style={{ padding: '8px 18px', fontSize: 13 }}>
                  <Sparkles size={13} />
                  Get Started
                </Link>
              </>
            )}

            {/* Mobile Menu Button */}
            <motion.button
              whileTap={{ scale: 0.9 }}
              onClick={() => setMobileOpen(!mobileOpen)}
              className="btn-ghost mobile-menu-btn"
              style={{ padding: '7px', borderRadius: 2 }}
            >
              {mobileOpen ? <X size={19} /> : <Menu size={19} />}
            </motion.button>
          </div>
        </div>
      </motion.nav>

      {/* Mobile Menu — sharp rectangular panel */}
      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            initial={{ opacity: 0, y: -16 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -16 }}
            transition={{ duration: 0.18 }}
            style={{
              position: 'fixed',
              top: 72,
              left: 0,
              right: 0,
              zIndex: 999,
              background: darkMode ? 'rgba(13,17,23,0.98)' : 'rgba(255,255,255,0.98)',
              backdropFilter: 'blur(16px)',
              borderBottom: `1px solid ${darkMode ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.06)'}`,
              borderRadius: 0,
              padding: '12px 24px 20px',
            }}
          >
            {navLinks.map(({ path, label, icon: Icon }) => (
              <Link
                key={path}
                to={path}
                className={`nav-link ${location.pathname === path ? 'active' : ''}`}
                style={{ display: 'flex', padding: '11px 14px', marginBottom: 3, borderRadius: 2 }}
                onClick={() => setMobileOpen(false)}
              >
                <Icon size={15} style={{ marginRight: 10 }} />
                {label}
              </Link>
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      <style>{`
        @media (min-width: 769px) { .mobile-menu-btn { display: none !important; } }
        @media (max-width: 768px) { .desktop-nav { display: none !important; } }
        @media (max-width: 480px) {
          .btn-primary { display: none; }
        }
      `}</style>
    </>
  );
};
