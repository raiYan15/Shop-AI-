import React, { useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { Brain, Cpu, Activity, Gauge, Moon, Sun } from 'lucide-react';
import { useStore } from '../../store/useStore';
import '../../styles/auth.css';

interface AuthShellProps {
  panelTitle: string;
  panelSubtitle: string;
  children: React.ReactNode;
}

const metrics = [
  { label: 'AI Accuracy', value: '98.7%', icon: Cpu },
  { label: 'Products Indexed', value: '1.2 Million+', icon: Activity },
  { label: 'Recommendation Precision', value: '96%', icon: Gauge },
  { label: 'Search Response Time', value: '<100ms', icon: Activity },
];

const neuralNodes = Array.from({ length: 26 }, (_, i) => {
  const seed = i + 1;
  return {
    id: i,
    top: `${(seed * 17) % 100}%`,
    left: `${(seed * 31) % 100}%`,
    duration: 6 + (seed % 5),
    delay: (seed % 7) * 0.35,
  };
});

export const AuthShell: React.FC<AuthShellProps> = ({ panelTitle, panelSubtitle, children }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const { darkMode, toggleDarkMode } = useStore();

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let raf = 0;
    const nodes = Array.from({ length: 40 }, () => ({
      x: Math.random() * canvas.clientWidth,
      y: Math.random() * canvas.clientHeight,
      vx: (Math.random() - 0.5) * 0.42,
      vy: (Math.random() - 0.5) * 0.42,
      radius: 1 + Math.random() * 1.5,
    }));

    const resize = () => {
      canvas.width = canvas.clientWidth;
      canvas.height = canvas.clientHeight;
    };

    const draw = () => {
      if (!ctx) return;
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      for (const n of nodes) {
        n.x += n.vx;
        n.y += n.vy;
        if (n.x <= 0 || n.x >= canvas.width) n.vx *= -1;
        if (n.y <= 0 || n.y >= canvas.height) n.vy *= -1;
      }

      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const a = nodes[i];
          const b = nodes[j];
          const dx = a.x - b.x;
          const dy = a.y - b.y;
          const dist = Math.sqrt(dx * dx + dy * dy);

          if (dist < 120) {
            const alpha = (1 - dist / 120) * 0.18;
            ctx.strokeStyle = `rgba(255,153,0,${alpha})`;
            ctx.lineWidth = 0.7;
            ctx.beginPath();
            ctx.moveTo(a.x, a.y);
            ctx.lineTo(b.x, b.y);
            ctx.stroke();
          }
        }
      }

      for (const n of nodes) {
        ctx.beginPath();
        ctx.arc(n.x, n.y, n.radius, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(255,153,0,0.45)';
        ctx.fill();
      }

      raf = requestAnimationFrame(draw);
    };

    resize();
    draw();
    window.addEventListener('resize', resize);

    return () => {
      window.removeEventListener('resize', resize);
      cancelAnimationFrame(raf);
    };
  }, []);

  return (
    <div className="auth-root">
      <section className="auth-brand-panel" aria-hidden="true">
        <div className="auth-grid-overlay" />
        <canvas ref={canvasRef} className="auth-network-canvas" />

        <div className="auth-particles-layer">
          {neuralNodes.map((node) => (
            <span
              key={node.id}
              className="auth-particle"
              style={{
                top: node.top,
                left: node.left,
                animationDuration: `${node.duration}s`,
                animationDelay: `${node.delay}s`,
              }}
            />
          ))}
        </div>

        <div className="auth-brand-content">
          <div className="auth-brand-head">
            <div className="auth-brand-logo">
              <Brain size={24} />
            </div>
            <div>
              <h1 className="auth-brand-title">ShopMind AI</h1>
              <p className="auth-brand-tag">Enterprise Commerce Intelligence</p>
            </div>
          </div>

          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.45 }}
            className="auth-hero-copy"
          >
            <h2>Shop Smarter with AI</h2>
            <p>
              Discover products through semantic search, personalized recommendations,
              intelligent ranking, and AI-powered shopping assistance.
            </p>
          </motion.div>

          <div className="auth-metrics-grid">
            {metrics.map((metric, index) => {
              const Icon = metric.icon;
              return (
                <motion.article
                  key={metric.label}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.4, delay: 0.1 + index * 0.07 }}
                  className="auth-metric-card"
                >
                  <header>
                    <Icon size={15} />
                    <span>{metric.label}</span>
                  </header>
                  <strong>{metric.value}</strong>
                </motion.article>
              );
            })}
          </div>
        </div>
      </section>

      <section className="auth-form-panel">
        <div className="auth-form-topbar">
          <div className="auth-mini-brand">
            <Brain size={17} />
            <span>ShopMind AI</span>
          </div>
          <button
            type="button"
            className="auth-theme-btn"
            onClick={toggleDarkMode}
            aria-label="Toggle theme"
            title="Toggle theme"
          >
            {darkMode ? <Sun size={16} /> : <Moon size={16} />}
          </button>
        </div>

        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="auth-form-wrap"
        >
          <header className="auth-form-header">
            <h2>{panelTitle}</h2>
            <p>{panelSubtitle}</p>
          </header>

          {children}
        </motion.div>
      </section>
    </div>
  );
};

export default AuthShell;
