import React from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { Heart, Eye, Zap, ShoppingCart } from 'lucide-react';
import { Product } from '../../data/mockData';
import { useStore } from '../../store/useStore';

interface ProductCardProps {
  product: Product;
  index?: number;
  layout?: 'grid' | 'list';
}

const formatPrice = (price: number) =>
  '₹' + price.toLocaleString('en-IN');

const StarRating: React.FC<{ rating: number; size?: number }> = ({ rating, size = 12 }) => (
  <div style={{ display: 'flex', alignItems: 'center', gap: 1 }}>
    {[1, 2, 3, 4, 5].map((star) => (
      <svg key={star} width={size} height={size} viewBox="0 0 24 24" fill={star <= Math.round(rating) ? '#FF9900' : 'none'} stroke="#FF9900" strokeWidth="2">
        <polygon points="12,2 15.09,8.26 22,9.27 17,14.14 18.18,21.02 12,17.77 5.82,21.02 7,14.14 2,9.27 8.91,8.26" />
      </svg>
    ))}
  </div>
);

export const ProductCard: React.FC<ProductCardProps> = ({ product, index = 0 }) => {
  const { toggleWishlist, isInWishlist, addToCart } = useStore();
  const inWishlist = isInWishlist(product.id);

  return (
    <motion.div
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05, duration: 0.35 }}
      whileHover={{ y: -4 }}
      style={{ position: 'relative' }}
    >
      {/*
        Product card — sharp rectangular panel.
        Engineered feel: strong border, precise grid, no soft rounded corners.
        Inspired by premium e-commerce management interfaces.
      */}
      <div
        style={{
          background: 'var(--bg-card)',
          border: '1px solid var(--border-color)',
          /* SHARP — 2px maximum */
          borderRadius: 2,
          overflow: 'hidden',
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          transition: 'border-color 0.2s, box-shadow 0.2s',
          cursor: 'pointer',
          boxShadow: '0 1px 4px rgba(0,0,0,0.07)',
        }}
        onMouseEnter={(e) => {
          (e.currentTarget as HTMLElement).style.borderColor = 'rgba(255,153,0,0.4)';
          (e.currentTarget as HTMLElement).style.boxShadow = '0 4px 20px rgba(0,0,0,0.14)';
        }}
        onMouseLeave={(e) => {
          (e.currentTarget as HTMLElement).style.borderColor = 'var(--border-color)';
          (e.currentTarget as HTMLElement).style.boxShadow = '0 1px 4px rgba(0,0,0,0.07)';
        }}
      >
        {/* Image Container — sharp frame */}
        <Link to={`/products/${product.id}`} style={{ textDecoration: 'none', display: 'block', position: 'relative' }}>
          <div style={{
            position: 'relative',
            height: 210,
            overflow: 'hidden',
            background: '#F7F8F8',
            borderBottom: '1px solid var(--border-color)',
          }}>
            <motion.img
              src={product.image}
              alt={product.name}
              loading="lazy"
              whileHover={{ scale: 1.05 }}
              transition={{ duration: 0.35 }}
              style={{
                width: '100%',
                height: '100%',
                objectFit: 'cover',
              }}
            />

            {/* Dark overlay on hover */}
            <div style={{
              position: 'absolute', inset: 0,
              background: 'linear-gradient(to top, rgba(0,0,0,0.25) 0%, transparent 60%)',
              opacity: 0,
              transition: 'opacity 0.25s',
            }} />

            {/* Badge — sharp rectangle */}
            {product.badge && (
              <div style={{ position: 'absolute', top: 10, left: 10 }}>
                <span className="badge badge-orange">{product.badge}</span>
              </div>
            )}

            {/* Discount tag — sharp rectangle with strong color */}
            {product.discount > 0 && (
              <div style={{ position: 'absolute', top: 10, right: 10 }}>
                <span style={{
                  background: '#B12704', color: 'white',
                  padding: '3px 7px',
                  /* Sharp — 2px max */
                  borderRadius: 2,
                  fontSize: 11, fontWeight: 700,
                  fontFamily: 'JetBrains Mono, monospace',
                }}>
                  -{product.discount}%
                </span>
              </div>
            )}

            {/* Quick Cart overlay */}
            <motion.div
              initial={{ opacity: 0 }}
              whileHover={{ opacity: 1 }}
              style={{
                position: 'absolute', bottom: 10, left: '50%',
                transform: 'translateX(-50%)',
                display: 'flex', gap: 6,
              }}
            >
              <motion.button
                whileHover={{ scale: 1.04 }}
                whileTap={{ scale: 0.96 }}
                onClick={(e) => { e.preventDefault(); addToCart(product); }}
                style={{
                  display: 'flex', alignItems: 'center', gap: 6,
                  padding: '7px 13px',
                  background: '#FF9900',
                  color: '#0D1117', border: 'none',
                  /* Sharp — not pill-shaped */
                  borderRadius: 2,
                  fontSize: 12, fontWeight: 700, cursor: 'pointer',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.3)',
                }}
              >
                <ShoppingCart size={12} />
                Add to Cart
              </motion.button>
            </motion.div>
          </div>
        </Link>

        {/* Content */}
        <div style={{ padding: '14px', display: 'flex', flexDirection: 'column', gap: 8, flex: 1 }}>
          {/* Category + Wishlist */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{
              fontSize: 10, fontWeight: 700, color: 'var(--text-secondary)',
              textTransform: 'uppercase', letterSpacing: '0.09em',
              background: 'rgba(255,153,0,0.06)',
              padding: '2px 6px',
              /* Category chip — sharp */
              borderRadius: 2,
              border: '1px solid rgba(255,153,0,0.12)',
              fontFamily: 'JetBrains Mono, monospace',
            }}>
              {product.category}
            </span>
            <motion.button
              whileHover={{ scale: 1.12 }}
              whileTap={{ scale: 0.88 }}
              onClick={() => toggleWishlist(product)}
              style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 3, borderRadius: 2, display: 'flex' }}
              aria-label={inWishlist ? 'Remove from wishlist' : 'Add to wishlist'}
            >
              <Heart
                size={16}
                fill={inWishlist ? '#EF4444' : 'none'}
                stroke={inWishlist ? '#EF4444' : 'currentColor'}
                color={inWishlist ? '#EF4444' : 'var(--text-secondary)'}
              />
            </motion.button>
          </div>

          {/* Name */}
          <Link to={`/products/${product.id}`} style={{ textDecoration: 'none' }}>
            <h3 style={{
              fontSize: 13, fontWeight: 600,
              color: 'var(--text-primary)',
              lineHeight: 1.4,
              display: '-webkit-box',
              WebkitLineClamp: 2,
              WebkitBoxOrient: 'vertical',
              overflow: 'hidden',
              margin: 0,
            }}>
              {product.name}
            </h3>
          </Link>

          {/* Rating */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <StarRating rating={product.rating} />
            <span style={{ fontSize: 12, fontWeight: 700, color: '#FF9900', fontFamily: 'JetBrains Mono, monospace' }}>{product.rating}</span>
            <span style={{ fontSize: 11, color: 'var(--text-secondary)' }}>({product.reviewCount.toLocaleString()})</span>
          </div>

          {/* AI Score — sharp rectangular progress bar */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <Zap size={11} color="#FF9900" />
            <span style={{ fontSize: 10, color: 'var(--text-secondary)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em' }}>AI</span>
            <div style={{
              flex: 1, height: 3,
              /* Sharp rectangular bar — not pill */
              borderRadius: 0,
              background: 'rgba(255,153,0,0.12)',
              overflow: 'hidden',
            }}>
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${product.aiScore}%` }}
                transition={{ delay: index * 0.05 + 0.3, duration: 0.8 }}
                style={{ height: '100%', borderRadius: 0, background: '#FF9900' }}
              />
            </div>
            <span style={{ fontSize: 11, fontWeight: 700, color: '#FF9900', fontFamily: 'JetBrains Mono, monospace' }}>{product.aiScore}</span>
          </div>

          {/* Price */}
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, marginTop: 'auto', paddingTop: 6, borderTop: '1px solid var(--border-color)' }}>
            <span style={{ fontFamily: 'Outfit, sans-serif', fontWeight: 800, fontSize: 19, color: 'var(--text-primary)' }}>
              {formatPrice(product.price)}
            </span>
            {product.originalPrice > product.price && (
              <span style={{ fontSize: 12, color: 'var(--text-secondary)', textDecoration: 'line-through' }}>
                {formatPrice(product.originalPrice)}
              </span>
            )}
          </div>

          {/* Quick View — sharp button */}
          <Link to={`/products/${product.id}`} style={{ textDecoration: 'none' }}>
            <motion.div
              whileHover={{ scale: 1.01 }}
              whileTap={{ scale: 0.99 }}
              style={{
                display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 5,
                padding: '8px',
                background: 'rgba(255,153,0,0.06)',
                border: '1px solid rgba(255,153,0,0.18)',
                /* Sharp — 2px */
                borderRadius: 2,
                color: '#FF9900', fontSize: 12, fontWeight: 700,
                cursor: 'pointer', transition: 'all 0.15s',
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
              }}
            >
              <Eye size={13} />
              Quick View
            </motion.div>
          </Link>
        </div>
      </div>
    </motion.div>
  );
};
