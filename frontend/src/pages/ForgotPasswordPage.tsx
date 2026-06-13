import React, { useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Mail, ArrowRight, AlertCircle, CheckCircle2, RotateCcw } from 'lucide-react';
import AuthShell from '../components/auth/AuthShell';

export const ForgotPasswordPage: React.FC = () => {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState('');

  const emailError = useMemo(() => {
    if (!email.trim()) return 'Email is required.';
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return 'Enter a valid email address.';
    return '';
  }, [email]);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (emailError) {
      setError(emailError);
      return;
    }

    setError('');
    setIsLoading(true);

    await new Promise((resolve) => setTimeout(resolve, 800));
    setSent(true);
    setIsLoading(false);
  };

  return (
    <AuthShell
      panelTitle="Recover Your Account"
      panelSubtitle="We’ll send a secure reset link to your registered email."
    >
      {!sent ? (
        <form className="auth-form" onSubmit={submit} noValidate aria-label="Forgot password form">
          <div className="auth-input-group">
            <label htmlFor="recover-email" className="auth-label">Work Email</label>
            <div className="auth-input-wrap">
              <Mail size={16} className="auth-input-icon" />
              <input
                id="recover-email"
                type="email"
                autoComplete="email"
                className={`auth-input ${error ? 'invalid' : ''}`}
                placeholder="you@company.com"
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value);
                  setError('');
                }}
              />
            </div>
            {error ? (
              <p className="auth-message error" role="alert">
                <AlertCircle size={14} /> {error}
              </p>
            ) : null}
          </div>

          <button type="submit" className="auth-submit" disabled={isLoading || Boolean(emailError)}>
            {isLoading ? (
              <>
                <span className="auth-spinner" /> Sending recovery email...
              </>
            ) : (
              <>
                Send Recovery Link <ArrowRight size={16} />
              </>
            )}
          </button>

          <p className="auth-footer-note">
            Remembered your password? <Link to="/signin" className="auth-link">Sign In</Link>
          </p>
        </form>
      ) : (
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="auth-form">
          <article className="auth-state-card" role="status" aria-live="polite">
            <p className="auth-message success">
              <CheckCircle2 size={16} /> Recovery email sent to {email}
            </p>
            <p className="auth-footer-note auth-footer-note-left">
              Open your mailbox and follow the reset link. If you don't see it, check spam/promotions.
            </p>
          </article>

          <button type="button" className="auth-submit" onClick={() => navigate(`/verify-email?email=${encodeURIComponent(email)}&status=pending`)}>
            Continue to Verification <ArrowRight size={16} />
          </button>

          <button
            type="button"
            className="auth-social"
            onClick={() => setSent(false)}
            aria-label="Resend reset email"
          >
            <RotateCcw size={15} /> Use another email
          </button>
        </motion.div>
      )}
    </AuthShell>
  );
};

export default ForgotPasswordPage;
