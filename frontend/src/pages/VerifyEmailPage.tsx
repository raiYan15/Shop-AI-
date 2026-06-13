import React, { useEffect, useMemo, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import { CheckCircle2, AlertCircle, RotateCcw, MailCheck } from 'lucide-react';
import AuthShell from '../components/auth/AuthShell';

type VerifyStatus = 'pending' | 'verifying' | 'success' | 'error';

export const VerifyEmailPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const [status, setStatus] = useState<VerifyStatus>('pending');
  const [isResending, setIsResending] = useState(false);

  const email = searchParams.get('email') || 'your inbox';
  const initialStatus = searchParams.get('status') as VerifyStatus | null;

  useEffect(() => {
    if (initialStatus === 'success' || initialStatus === 'error') {
      setStatus(initialStatus);
      return;
    }

    setStatus('verifying');
    const timer = setTimeout(() => setStatus('success'), 1300);
    return () => clearTimeout(timer);
  }, [initialStatus]);

  const statusData = useMemo(() => {
    if (status === 'success') {
      return {
        icon: <CheckCircle2 size={18} />,
        className: 'success' as const,
        title: 'Email verified successfully',
        description: 'Your account is now ready. Continue to sign in and access the AI commerce dashboard.',
      };
    }

    if (status === 'error') {
      return {
        icon: <AlertCircle size={18} />,
        className: 'error' as const,
        title: 'Verification link is invalid or expired',
        description: 'Request a new verification email and try again.',
      };
    }

    return {
      icon: <MailCheck size={18} />,
      className: 'success' as const,
      title: status === 'verifying' ? 'Verifying your email...' : 'Verification pending',
      description: 'We are validating your secure token. This only takes a moment.',
    };
  }, [status]);

  const resend = async () => {
    setIsResending(true);
    await new Promise((resolve) => setTimeout(resolve, 800));
    setStatus('success');
    setIsResending(false);
  };

  return (
    <AuthShell
      panelTitle="Email Verification"
      panelSubtitle="Securely verify your identity before continuing."
    >
      <motion.div className="auth-form" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
        <article className="auth-state-card" role="status" aria-live="polite">
          <p className={`auth-message ${statusData.className}`}>
            {statusData.icon}
            {statusData.title}
          </p>
          <p className="auth-footer-note auth-footer-note-left">
            {statusData.description}
          </p>
          <p className="auth-footer-note auth-footer-note-left">
            Verification target: <strong>{email}</strong>
          </p>
        </article>

        <Link to="/signin" className="auth-submit auth-submit-link">
          Continue to Sign In
        </Link>

        <button type="button" className="auth-social" onClick={resend} disabled={isResending}>
          {isResending ? <span className="auth-spinner" /> : <RotateCcw size={15} />}
          {isResending ? 'Resending...' : 'Resend verification email'}
        </button>

        <p className="auth-footer-note">
          Need to reset account access? <Link to="/forgot-password" className="auth-link">Recover Account</Link>
        </p>
      </motion.div>
    </AuthShell>
  );
};

export default VerifyEmailPage;
