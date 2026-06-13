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
  Phone,
  User,
  Globe,
  GitBranch,
} from 'lucide-react';
import AuthShell from '../components/auth/AuthShell';
import { signUp, saveAuth } from '../services/api';
import { useStore } from '../store/useStore';

interface SignUpForm {
  firstName: string;
  lastName: string;
  email: string;
  phone: string;
  password: string;
  confirmPassword: string;
  agreeToTerms: boolean;
}

function getPasswordStrength(password: string): number {
  let score = 0;
  if (password.length >= 8) score += 1;
  if (/[A-Z]/.test(password) && /[a-z]/.test(password)) score += 1;
  if (/\d/.test(password)) score += 1;
  if (/[^A-Za-z0-9]/.test(password)) score += 1;
  return score;
}

export const SignUpPage: React.FC = () => {
  const navigate = useNavigate();
  const setCurrentUser = useStore((s) => s.setCurrentUser);

  const [form, setForm] = useState<SignUpForm>({
    firstName: '',
    lastName: '',
    email: '',
    phone: '',
    password: '',
    confirmPassword: '',
    agreeToTerms: false,
  });

  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [globalError, setGlobalError] = useState('');
  const [success, setSuccess] = useState(false);
  const [touched, setTouched] = useState<Record<string, boolean>>({});

  const passwordStrength = getPasswordStrength(form.password);

  const errors = useMemo(() => {
    const next: Record<string, string> = {};

    if (!form.firstName.trim()) next.firstName = 'First name is required.';
    if (!form.lastName.trim()) next.lastName = 'Last name is required.';

    if (!form.email.trim()) next.email = 'Email is required.';
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) next.email = 'Enter a valid email.';

    if (!form.password) next.password = 'Password is required.';
    else if (form.password.length < 8) next.password = 'Password must be at least 8 characters.';

    if (!form.confirmPassword) next.confirmPassword = 'Please confirm your password.';
    else if (form.confirmPassword !== form.password) next.confirmPassword = 'Passwords do not match.';

    if (!form.agreeToTerms) next.terms = 'Please accept the Terms and Privacy Policy.';

    return next;
  }, [form]);

  const canSubmit = Object.keys(errors).length === 0 && !isLoading;

  const setField = <K extends keyof SignUpForm>(field: K, value: SignUpForm[K]) => {
    setForm((prev) => ({ ...prev, [field]: value }));
    setGlobalError('');
  };

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setTouched({
      firstName: true,
      lastName: true,
      email: true,
      password: true,
      confirmPassword: true,
      terms: true,
    });

    if (Object.keys(errors).length > 0) return;

    setIsLoading(true);
    setGlobalError('');

    try {
      const res = await signUp({
        email: form.email.trim(),
        password: form.password,
        first_name: form.firstName.trim(),
        last_name: form.lastName.trim(),
        phone: form.phone.trim(),
      });

      saveAuth(res);
      setCurrentUser(res.user);
      setSuccess(true);
      setTimeout(() => navigate('/verify-email?status=pending'), 700);
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : 'Unable to create account right now.';
      setGlobalError(message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AuthShell
      panelTitle="Create Account"
      panelSubtitle="Build your AI-powered shopping workspace in seconds."
    >
      <form className="auth-form" onSubmit={onSubmit} noValidate aria-label="Sign up form">
        <div className="auth-input-row">
          <div className="auth-input-group">
            <label htmlFor="signup-first-name" className="auth-label">First Name</label>
            <div className="auth-input-wrap">
              <User size={16} className="auth-input-icon" />
              <input
                id="signup-first-name"
                type="text"
                autoComplete="given-name"
                className={`auth-input ${touched.firstName && errors.firstName ? 'invalid' : touched.firstName && !errors.firstName ? 'success' : ''}`}
                value={form.firstName}
                onBlur={() => setTouched((prev) => ({ ...prev, firstName: true }))}
                onChange={(e) => setField('firstName', e.target.value)}
              />
            </div>
            {touched.firstName && errors.firstName ? <p className="auth-message error"><AlertCircle size={14} />{errors.firstName}</p> : null}
          </div>

          <div className="auth-input-group">
            <label htmlFor="signup-last-name" className="auth-label">Last Name</label>
            <div className="auth-input-wrap">
              <User size={16} className="auth-input-icon" />
              <input
                id="signup-last-name"
                type="text"
                autoComplete="family-name"
                className={`auth-input ${touched.lastName && errors.lastName ? 'invalid' : touched.lastName && !errors.lastName ? 'success' : ''}`}
                value={form.lastName}
                onBlur={() => setTouched((prev) => ({ ...prev, lastName: true }))}
                onChange={(e) => setField('lastName', e.target.value)}
              />
            </div>
            {touched.lastName && errors.lastName ? <p className="auth-message error"><AlertCircle size={14} />{errors.lastName}</p> : null}
          </div>
        </div>

        <div className="auth-input-group">
          <label htmlFor="signup-email" className="auth-label">Email</label>
          <div className="auth-input-wrap">
            <Mail size={16} className="auth-input-icon" />
            <input
              id="signup-email"
              type="email"
              autoComplete="email"
              className={`auth-input ${touched.email && errors.email ? 'invalid' : touched.email && !errors.email ? 'success' : ''}`}
              placeholder="you@company.com"
              value={form.email}
              onBlur={() => setTouched((prev) => ({ ...prev, email: true }))}
              onChange={(e) => setField('email', e.target.value)}
            />
          </div>
          {touched.email && errors.email ? <p className="auth-message error"><AlertCircle size={14} />{errors.email}</p> : null}
        </div>

        <div className="auth-input-group">
          <label htmlFor="signup-phone" className="auth-label">Phone Number (Optional)</label>
          <div className="auth-input-wrap">
            <Phone size={16} className="auth-input-icon" />
            <input
              id="signup-phone"
              type="tel"
              autoComplete="tel"
              className="auth-input"
              placeholder="+1 555 000 1234"
              value={form.phone}
              onChange={(e) => setField('phone', e.target.value)}
            />
          </div>
        </div>

        <div className="auth-input-group">
          <label htmlFor="signup-password" className="auth-label">Password</label>
          <div className="auth-input-wrap">
            <Lock size={16} className="auth-input-icon" />
            <input
              id="signup-password"
              type={showPassword ? 'text' : 'password'}
              autoComplete="new-password"
              className={`auth-input ${touched.password && errors.password ? 'invalid' : touched.password && !errors.password ? 'success' : ''}`}
              placeholder="Create a strong password"
              value={form.password}
              onBlur={() => setTouched((prev) => ({ ...prev, password: true }))}
              onChange={(e) => setField('password', e.target.value)}
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
            <p className="auth-message error"><AlertCircle size={14} />{errors.password}</p>
          ) : null}

          <div className="auth-password-meter" aria-live="polite">
            <span className="auth-label auth-meter-label">Password strength</span>
            <div className="auth-meter-track" aria-label="Password strength indicator">
              {[1, 2, 3, 4].map((level) => (
                <span
                  key={level}
                  className={`auth-meter-segment ${passwordStrength >= level ? `active-${Math.min(passwordStrength, 4)}` : ''}`}
                />
              ))}
            </div>
          </div>
        </div>

        <div className="auth-input-group">
          <label htmlFor="signup-confirm-password" className="auth-label">Confirm Password</label>
          <div className="auth-input-wrap">
            <Lock size={16} className="auth-input-icon" />
            <input
              id="signup-confirm-password"
              type={showConfirmPassword ? 'text' : 'password'}
              autoComplete="new-password"
              className={`auth-input ${touched.confirmPassword && errors.confirmPassword ? 'invalid' : touched.confirmPassword && !errors.confirmPassword ? 'success' : ''}`}
              placeholder="Re-enter password"
              value={form.confirmPassword}
              onBlur={() => setTouched((prev) => ({ ...prev, confirmPassword: true }))}
              onChange={(e) => setField('confirmPassword', e.target.value)}
            />
            <button
              type="button"
              className="auth-toggle-btn"
              onClick={() => setShowConfirmPassword((prev) => !prev)}
              aria-label={showConfirmPassword ? 'Hide confirm password' : 'Show confirm password'}
            >
              {showConfirmPassword ? <EyeOff size={16} /> : <Eye size={16} />}
            </button>
          </div>
          {touched.confirmPassword && errors.confirmPassword ? (
            <p className="auth-message error"><AlertCircle size={14} />{errors.confirmPassword}</p>
          ) : null}
        </div>

        <label className="auth-check">
          <input
            type="checkbox"
            checked={form.agreeToTerms}
            onChange={(e) => {
              setField('agreeToTerms', e.target.checked);
              setTouched((prev) => ({ ...prev, terms: true }));
            }}
          />
          I agree to the <Link to="/terms" className="auth-link">Terms</Link> and <Link to="/privacy" className="auth-link">Privacy Policy</Link>.
        </label>

        {touched.terms && errors.terms ? <p className="auth-message error"><AlertCircle size={14} />{errors.terms}</p> : null}

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
            <CheckCircle2 size={14} /> Account created. Redirecting to verification…
          </motion.p>
        ) : null}

        <button type="submit" className="auth-submit" disabled={!canSubmit}>
          {isLoading ? (
            <>
              <span className="auth-spinner" />
              Creating Account...
            </>
          ) : (
            <>
              Create Account
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
          Already have an account? <Link to="/signin" className="auth-link">Sign In</Link>
        </p>
      </form>
    </AuthShell>
  );
};

export default SignUpPage;
