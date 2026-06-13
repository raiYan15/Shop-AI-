import React, { useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Mail,
  Lock,
  Eye,
  EyeOff,
  ArrowRight,
  AlertCircle,
  CheckCircle2,
  GitBranch,
  Globe,
} from 'lucide-react';
import AuthShell from '../components/auth/AuthShell';
import { signIn, saveAuth } from '../services/api';
import { useStore } from '../store/useStore';

interface FormState {
  email: string;
  password: string;
  rememberMe: boolean;
}

export const SignInPage: React.FC = () => {
  const navigate = useNavigate();
  const setCurrentUser = useStore((s) => s.setCurrentUser);

  const [form, setForm] = useState<FormState>({ email: '', password: '', rememberMe: true });
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [globalError, setGlobalError] = useState('');
  const [success, setSuccess] = useState(false);
  const [touched, setTouched] = useState<{ email?: boolean; password?: boolean }>({});

  const errors = useMemo(() => {
    const next: { email?: string; password?: string } = {};
    if (!form.email.trim()) next.email = 'Email is required.';
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) next.email = 'Enter a valid email.';

    if (!form.password) next.password = 'Password is required.';
    else if (form.password.length < 8) next.password = 'Password must be at least 8 characters.';

    return next;
  }, [form.email, form.password]);

  const canSubmit = Object.keys(errors).length === 0 && !isLoading;

  const updateField = (field: keyof FormState, value: string | boolean) => {
    setForm((prev) => ({ ...prev, [field]: value }));
    setGlobalError('');
  };

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setTouched({ email: true, password: true });
    if (Object.keys(errors).length > 0) return;

    setIsLoading(true);
    setGlobalError('');

    try {
      const res = await signIn({
        email: form.email.trim(),
        password: form.password,
      });

      saveAuth(res);
      setCurrentUser(res.user);
      setSuccess(true);
      setTimeout(() => navigate('/'), 700);
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : 'Unable to sign in right now.';
      setGlobalError(message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AuthShell
      panelTitle="Welcome Back"
      panelSubtitle="Continue your AI-powered shopping journey."
    >
      <form className="auth-form" onSubmit={onSubmit} noValidate aria-label="Sign in form">
        <div className="auth-input-group">
          <label htmlFor="signin-email" className="auth-label">Email</label>
          <div className="auth-input-wrap">
            <Mail size={16} className="auth-input-icon" />
            <input
              id="signin-email"
              name="email"
              type="email"
              autoComplete="email"
              className={`auth-input ${touched.email && errors.email ? 'invalid' : touched.email && !errors.email ? 'success' : ''}`}
              placeholder="you@company.com"
              value={form.email}
              onBlur={() => setTouched((prev) => ({ ...prev, email: true }))}
              onChange={(e) => updateField('email', e.target.value)}
              aria-describedby={touched.email && errors.email ? 'signin-email-error' : undefined}
            />
          </div>
          {touched.email && errors.email ? (
            <p id="signin-email-error" className="auth-message error">
              <AlertCircle size={14} /> {errors.email}
            </p>
          ) : null}
        </div>

        <div className="auth-input-group">
          <label htmlFor="signin-password" className="auth-label">Password</label>
          <div className="auth-input-wrap">
            <Lock size={16} className="auth-input-icon" />
            <input
              id="signin-password"
              name="password"
              type={showPassword ? 'text' : 'password'}
              autoComplete="current-password"
              className={`auth-input ${touched.password && errors.password ? 'invalid' : touched.password && !errors.password ? 'success' : ''}`}
              placeholder="••••••••"
              value={form.password}
              onBlur={() => setTouched((prev) => ({ ...prev, password: true }))}
              onChange={(e) => updateField('password', e.target.value)}
              aria-describedby={touched.password && errors.password ? 'signin-password-error' : undefined}
            />
            <button
              type="button"
              className="auth-toggle-btn"
              onClick={() => setShowPassword((prev) => !prev)}
              aria-label={showPassword ? 'Hide password' : 'Show password'}
            >
              {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
            </button>
          </div>
          {touched.password && errors.password ? (
            <p id="signin-password-error" className="auth-message error">
              <AlertCircle size={14} /> {errors.password}
            </p>
          ) : null}
        </div>

        <div className="auth-meta-row">
          <label className="auth-check">
            <input
              type="checkbox"
              checked={form.rememberMe}
              onChange={(e) => updateField('rememberMe', e.target.checked)}
            />
            Remember me
          </label>
          <Link to="/forgot-password" className="auth-link">Forgot Password?</Link>
        </div>

        {globalError ? (
          <p className="auth-message error" role="alert">
            <AlertCircle size={14} />
            {globalError}
          </p>
        ) : null}

        {success ? (
          <motion.p
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            className="auth-message success"
            role="status"
          >
            <CheckCircle2 size={14} /> Sign in successful. Redirecting…
          </motion.p>
        ) : null}

        <button type="submit" className="auth-submit" disabled={!canSubmit}>
          {isLoading ? (
            <>
              <span className="auth-spinner" />
              Signing In...
            </>
          ) : (
            <>
              Sign In
              <ArrowRight size={16} />
            </>
          )}
        </button>

        <div className="auth-divider">or continue with</div>

        <div className="auth-social-grid">
          <button
            type="button"
            className="auth-social"
            onClick={() => setGlobalError('Google SSO will be enabled in the next release.')}
            aria-label="Continue with Google"
          >
            <Globe size={16} /> Google
          </button>
          <button
            type="button"
            className="auth-social"
            onClick={() => setGlobalError('GitHub SSO will be enabled in the next release.')}
            aria-label="Continue with GitHub"
          >
            <GitBranch size={16} /> GitHub
          </button>
        </div>

        <p className="auth-footer-note">
          Don&apos;t have an account? <Link to="/signup" className="auth-link">Create Account</Link>
        </p>
      </form>
    </AuthShell>
  );
};

export default SignInPage;
