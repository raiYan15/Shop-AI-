import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useParams, Link, useNavigate } from 'react-router-dom';
import {
  Star, Heart, ShoppingCart, Truck, Shield, RotateCcw,
  ChevronLeft, ChevronRight, ArrowLeft, Zap, GitCompare
} from 'lucide-react';
import { MOCK_PRODUCTS } from '../data/mockData';
import { AiInsightsPanel } from '../components/ai/AiInsightsPanel';
import { ProductCard } from '../components/ui/ProductCard';
import { Footer } from '../components/layout/Footer';
import { useStore } from '../store/useStore';

const formatPrice = (price: number) => '₹' + price.toLocaleString('en-IN');

export const ProductDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { addToCart, toggleWishlist, isInWishlist } = useStore();
  const product = MOCK_PRODUCTS.find((p) => p.id === id);
  const [selectedImage, setSelectedImage] = useState(0);
  const [quantity, setQuantity] = useState(1);
  const [addedToCart, setAddedToCart] = useState(false);

  if (!product) {
    return (
      <div className="page-wrapper" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '80vh' }}>
        <div style={{ textAlign: 'center' }}>
          <h2 style={{ color: 'var(--text-primary)', marginBottom: 12 }}>Product not found</h2>
          <Link to="/products" className="btn-primary">Back to Products</Link>
        </div>
      </div>
    );
  }

  // Simulate multiple images
  const images = [product.image, product.image, product.image];
  const similarProducts = MOCK_PRODUCTS.filter((p) => p.category === product.category && p.id !== product.id).slice(0, 4);
  const inWishlist = isInWishlist(product.id);

  const handleAddToCart = () => {
    addToCart(product);
    setAddedToCart(true);
    setTimeout(() => setAddedToCart(false), 2000);
  };

  return (
    <div className="page-wrapper">
      <div className="container" style={{ paddingTop: 32 }}>
        {/* Breadcrumb */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 32 }}
        >
          <button
            onClick={() => navigate(-1)}
            className="btn-ghost"
            style={{ padding: '6px 12px', gap: 6 }}
          >
            <ArrowLeft size={14} />
            Back
          </button>
          <span style={{ color: 'var(--text-secondary)', fontSize: 13 }}>/</span>
          <Link to="/products" style={{ color: 'var(--text-secondary)', fontSize: 13, textDecoration: 'none' }}>Products</Link>
          <span style={{ color: 'var(--text-secondary)', fontSize: 13 }}>/</span>
          <span style={{ color: '#FF9900', fontSize: 13, fontWeight: 500 }}>{product.category}</span>
        </motion.div>

        {/* Main Layout */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))',
          gap: 32,
          marginBottom: 48,
        }}>
          {/* LEFT: Gallery */}
          <motion.div initial={{ opacity: 0, x: -30 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.5 }}>
            <div style={{ position: 'sticky', top: 90 }}>
              {/* Main Image */}
              <div style={{
                /* Sharp image frame — 2px */
                borderRadius: 2, overflow: 'hidden',
                background: '#F7F8F8',
                marginBottom: 12, position: 'relative',
                border: '1px solid var(--border-color)',
              }}>
                <AnimatePresence mode="wait">
                  <motion.img
                    key={selectedImage}
                    src={images[selectedImage]}
                    alt={product.name}
                    initial={{ opacity: 0, scale: 1.05 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.95 }}
                    transition={{ duration: 0.3 }}
                    style={{ width: '100%', height: 420, objectFit: 'cover', display: 'block' }}
                  />
                </AnimatePresence>

                {/* Navigation Arrows */}
                <button
                  onClick={() => setSelectedImage((prev) => (prev - 1 + images.length) % images.length)}
                  style={{
                    position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)',
                    width: 32, height: 32,
                    /* Sharp — 2px */
                    borderRadius: 2,
                    background: 'rgba(255,255,255,0.92)', border: '1px solid rgba(0,0,0,0.08)',
                    cursor: 'pointer',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    boxShadow: '0 2px 8px rgba(0,0,0,0.12)',
                  }}
                >
                  <ChevronLeft size={16} />
                </button>
                <button
                  onClick={() => setSelectedImage((prev) => (prev + 1) % images.length)}
                  style={{
                    position: 'absolute', right: 10, top: '50%', transform: 'translateY(-50%)',
                    width: 32, height: 32,
                    /* Sharp — 2px */
                    borderRadius: 2,
                    background: 'rgba(255,255,255,0.92)', border: '1px solid rgba(0,0,0,0.08)',
                    cursor: 'pointer',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    boxShadow: '0 2px 8px rgba(0,0,0,0.12)',
                  }}
                >
                  <ChevronRight size={16} />
                </button>

                {product.badge && (
                  <div style={{ position: 'absolute', top: 16, left: 16 }}>
                    <span className="badge badge-orange">{product.badge}</span>
                  </div>
                )}
              </div>

              {/* Thumbnails */}
              <div style={{ display: 'flex', gap: 10 }}>
                {images.map((img, i) => (
                  <motion.button
                    key={i}
                    whileHover={{ scale: 1.04 }}
                    onClick={() => setSelectedImage(i)}
                    style={{
                      flex: 1, height: 76,
                      /* Sharp — 2px */
                      borderRadius: 2,
                      border: selectedImage === i ? '2px solid #FF9900' : '1px solid var(--border-color)',
                      overflow: 'hidden', cursor: 'pointer', padding: 0,
                      boxShadow: selectedImage === i ? '0 0 0 3px rgba(255,153,0,0.15)' : 'none',
                    }}
                  >
                    <img src={img} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                  </motion.button>
                ))}
              </div>
            </div>
          </motion.div>

          {/* RIGHT: Product Info */}
          <motion.div initial={{ opacity: 0, x: 30 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.5 }}>
            {/* Brand */}
            <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-secondary)', letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: 8 }}>
              {product.brand} • {product.category}
            </div>

            {/* Name */}
            <h1 style={{
              fontFamily: 'Outfit, sans-serif', fontWeight: 800,
              fontSize: 'clamp(22px, 3vw, 32px)', color: 'var(--text-primary)',
              lineHeight: 1.2, letterSpacing: '-0.03em', marginBottom: 16,
            }}>
              {product.name}
            </h1>

            {/* Rating Row */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 20 }}>
              <div style={{ display: 'flex', gap: 2 }}>
                {[1, 2, 3, 4, 5].map((s) => (
                  <Star key={s} size={16} fill={s <= Math.round(product.rating) ? '#FF9900' : 'none'} stroke="#FF9900" />
                ))}
              </div>
              <span style={{ fontWeight: 700, fontSize: 16, color: '#FF9900' }}>{product.rating}</span>
              <span style={{ color: 'var(--text-secondary)', fontSize: 14 }}>({product.reviewCount.toLocaleString()} reviews)</span>
              <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                <Zap size={13} color="#FF9900" />
                <span style={{ fontSize: 12, fontWeight: 600, color: '#FF9900' }}>AI Score: {product.aiScore}/100</span>
              </div>
            </div>

            {/* Price Block */}
            {/* Price Block — sharp panel */}
            <div className="glass-card" style={{ borderRadius: 2, padding: '20px 24px', marginBottom: 20 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 14, flexWrap: 'wrap' }}>
                <span style={{
                  fontFamily: 'Outfit, sans-serif', fontWeight: 900,
                  fontSize: 34, color: 'var(--text-primary)',
                  letterSpacing: '-0.03em',
                }}>
                  {formatPrice(product.price)}
                </span>
                {product.originalPrice > product.price && (
                  <>
                    <span style={{ fontSize: 18, color: 'var(--text-secondary)', textDecoration: 'line-through' }}>
                      {formatPrice(product.originalPrice)}
                    </span>
                    <span style={{
                      background: '#B12704', color: 'white',
                      padding: '3px 9px',
                      /* Sharp discount badge — 2px */
                      borderRadius: 2,
                      fontSize: 12, fontWeight: 700,
                      fontFamily: 'JetBrains Mono, monospace',
                    }}>
                      -{product.discount}% OFF
                    </span>
                  </>
                )}
              </div>
              <div style={{ marginTop: 8 }}>
                <span style={{
                  fontSize: 12, color: '#10B981', fontWeight: 700,
                  background: 'rgba(16,185,129,0.08)', padding: '3px 10px',
                  /* Sharp status badge — 2px */
                  borderRadius: 2,
                  border: '1px solid rgba(16,185,129,0.2)',
                  fontFamily: 'JetBrains Mono, monospace',
                }}>
                  {product.inStock ? '✓ In Stock — Ships Today' : '⚠ Out of Stock'}
                </span>
              </div>
            </div>

            {/* Quantity — sharp */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 18 }}>
              <span style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)', textTransform: 'uppercase', letterSpacing: '0.05em', fontFamily: 'JetBrains Mono, monospace' }}>Qty:</span>
              <div style={{ display: 'flex', alignItems: 'center', border: '1.5px solid var(--border-color)', /* Sharp */ borderRadius: 2, overflow: 'hidden' }}>
                <button onClick={() => setQuantity((q) => Math.max(1, q - 1))} style={{ padding: '7px 13px', background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-primary)', fontSize: 18, borderRadius: 0 }}>−</button>
                <span style={{ padding: '7px 14px', fontSize: 14, fontWeight: 700, color: 'var(--text-primary)', borderLeft: '1px solid var(--border-color)', borderRight: '1px solid var(--border-color)', fontFamily: 'JetBrains Mono, monospace' }}>{quantity}</span>
                <button onClick={() => setQuantity((q) => q + 1)} style={{ padding: '7px 13px', background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-primary)', fontSize: 18, borderRadius: 0 }}>+</button>
              </div>
            </div>

            {/* Action Buttons */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginBottom: 24 }}>
              <motion.button
                whileHover={{ scale: 1.01 }}
                whileTap={{ scale: 0.99 }}
                className="btn-primary"
                style={{ justifyContent: 'center', fontSize: 16, padding: '15px 28px' }}
              >
                Buy Now — {formatPrice(product.price * quantity)}
              </motion.button>
              <div style={{ display: 'flex', gap: 12 }}>
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={handleAddToCart}
                  className="btn-secondary"
                  style={{
                    flex: 1, justifyContent: 'center', fontSize: 14,
                    color: addedToCart ? '#10B981' : 'var(--text-primary)',
                    borderColor: addedToCart ? '#10B981' : 'var(--border-color)',
                  }}
                >
                  <ShoppingCart size={15} />
                  {addedToCart ? 'Added!' : 'Add to Cart'}
                </motion.button>
                <motion.button
                  whileHover={{ scale: 1.04 }}
                  whileTap={{ scale: 0.96 }}
                  onClick={() => toggleWishlist(product)}
                  style={{
                    width: 44,
                    /* Sharp — 2px */
                    borderRadius: 2,
                    border: '1.5px solid var(--border-color)',
                    background: inWishlist ? 'rgba(239,68,68,0.08)' : 'var(--bg-card)',
                    cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center',
                    borderColor: inWishlist ? 'rgba(239,68,68,0.3)' : 'var(--border-color)',
                  }}
                >
                  <Heart size={17} fill={inWishlist ? '#EF4444' : 'none'} stroke={inWishlist ? '#EF4444' : 'var(--text-secondary)'} />
                </motion.button>
              </div>
            </div>

            {/* Trust Badges */}
            <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap' }}>
              {[
                { icon: Truck, text: 'Free Delivery' },
                { icon: Shield, text: '2 Year Warranty' },
                { icon: RotateCcw, text: '30-Day Returns' },
              ].map(({ icon: Icon, text }) => (
                <div key={text} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <Icon size={14} color="#10B981" />
                  <span style={{ fontSize: 12, color: 'var(--text-secondary)', fontWeight: 500 }}>{text}</span>
                </div>
              ))}
            </div>

            {/* Description */}
            <div style={{ marginTop: 28, paddingTop: 24, borderTop: '1px solid var(--border-color)' }}>
              <h3 style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 12 }}>About this product</h3>
              <p style={{ fontSize: 14, color: 'var(--text-secondary)', lineHeight: 1.8 }}>{product.description}</p>
            </div>
          </motion.div>
        </div>

        {/* AI Insights Panel */}
        <div style={{ marginBottom: 48 }}>
          <div className="section-label" style={{ marginBottom: 20 }}>AI Analysis</div>
          <AiInsightsPanel product={product} />
        </div>

        {/* Compare Button */}
        <div style={{ textAlign: 'center', marginBottom: 64 }}>
          <Link to="/comparison" className="btn-secondary" style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}>
            <GitCompare size={16} />
            Compare with Similar Products
          </Link>
        </div>

        {/* Similar Products */}
        {similarProducts.length > 0 && (
          <div style={{ marginBottom: 64 }}>
            <div className="section-label">Smart Recommendations</div>
            <h2 style={{ fontSize: 28, fontWeight: 800, color: 'var(--text-primary)', marginBottom: 28, letterSpacing: '-0.02em' }}>
              Similar Products You Might Love
            </h2>
            <div className="scroll-container">
              {similarProducts.map((product, i) => (
                <div key={product.id} style={{ minWidth: 280, maxWidth: 300 }}>
                  <ProductCard product={product} index={i} />
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
      <Footer />
    </div>
  );
};
