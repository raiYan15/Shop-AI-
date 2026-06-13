import React from 'react';
import { BrowserRouter as Router, Routes, Route, useLocation, Navigate } from 'react-router-dom';
import { AnimatePresence, motion } from 'framer-motion';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Navbar } from './components/layout/Navbar';
import { HomePage } from './pages/HomePage';
import { ProductsPage } from './pages/ProductsPage';
import { ProductDetailPage } from './pages/ProductDetailPage';
import { RecommendationsPage } from './pages/RecommendationsPage';
import { AssistantPage } from './pages/AssistantPage';
import { AnalyticsPage } from './pages/AnalyticsPage';
import { ProfilePage } from './pages/ProfilePage';
import { SignInPage } from './pages/SignInPage';
import { SignUpPage } from './pages/SignUpPage';
import { ForgotPasswordPage } from './pages/ForgotPasswordPage';
import { VerifyEmailPage } from './pages/VerifyEmailPage';
import { useStore } from './store/useStore';
import { clearAuth, getCurrentUser, getStoredToken, refreshSession } from './services/api';
import './index.css';

const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 5 * 60 * 1000 } },
});

const PageTransition: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const location = useLocation();
  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={location.pathname}
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -8 }}
        transition={{ duration: 0.25, ease: 'easeInOut' }}
      >
        {children}
      </motion.div>
    </AnimatePresence>
  );
};

const AUTH_PATHS = ['/signin', '/signup', '/forgot-password', '/verify-email'];

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const isAuthenticated = useStore((s) => s.isAuthenticated());
  const location = useLocation();
  if (!isAuthenticated) {
    return <Navigate to="/signin" state={{ from: location.pathname }} replace />;
  }
  return <>{children}</>;
};

const AppInner: React.FC = () => {
  const { darkMode, setCurrentUser } = useStore();
  const location = useLocation();
  const isAuthPage = AUTH_PATHS.includes(location.pathname);

  React.useEffect(() => {
    const bootstrapAuth = async () => {
      const token = getStoredToken();
      if (!token) {
        setCurrentUser(null);
        return;
      }
      try {
        const me = await getCurrentUser();
        setCurrentUser(me);
      } catch {
        try {
          const refreshed = await refreshSession();
          setCurrentUser(refreshed.user);
        } catch {
          clearAuth();
          setCurrentUser(null);
        }
      }
    };
    bootstrapAuth();
  }, [setCurrentUser]);

  // Apply dark class to html element based on store
  React.useEffect(() => {
    if (darkMode) document.documentElement.classList.add('dark');
    else document.documentElement.classList.remove('dark');
  }, [darkMode]);

  // Auth pages render full-screen without Navbar or page-wrapper padding
  if (isAuthPage) {
    return (
      <Routes location={location} key={location.pathname}>
        <Route path="/signin" element={<SignInPage />} />
        <Route path="/signup" element={<SignUpPage />} />
        <Route path="/forgot-password" element={<ForgotPasswordPage />} />
        <Route path="/verify-email" element={<VerifyEmailPage />} />
      </Routes>
    );
  }

  return (
    <div style={{
      minHeight: '100vh',
      background: 'var(--bg-primary)',
      color: 'var(--text-primary)',
      transition: 'background-color 0.3s, color 0.3s',
    }}>
      <Navbar />
      <PageTransition>
        <Routes location={location} key={location.pathname}>
          <Route path="/" element={<HomePage />} />
          <Route path="/products" element={<ProductsPage />} />
          <Route path="/products/:id" element={<ProductDetailPage />} />
          <Route path="/recommendations" element={<RecommendationsPage />} />
          <Route path="/assistant" element={<AssistantPage />} />
          <Route path="/analytics" element={<AnalyticsPage />} />
          <Route
            path="/profile"
            element={
              <ProtectedRoute>
                <ProfilePage />
              </ProtectedRoute>
            }
          />
          <Route path="*" element={
            <div className="page-wrapper" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '80vh', flexDirection: 'column', gap: 16 }}>
              <div style={{ fontSize: 72, fontFamily: 'Outfit, sans-serif', fontWeight: 900, color: '#FF9900' }}>404</div>
              <h1 style={{ fontSize: 28, color: 'var(--text-primary)', fontFamily: 'Outfit, sans-serif' }}>Page Not Found</h1>
              <p style={{ color: 'var(--text-secondary)' }}>The page you're looking for doesn't exist.</p>
              <a href="/" className="btn-primary" style={{ marginTop: 8 }}>Go Home</a>
            </div>
          } />
        </Routes>
      </PageTransition>
    </div>
  );
};

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <AppInner />
      </Router>
    </QueryClientProvider>
  );
}

export default App;
