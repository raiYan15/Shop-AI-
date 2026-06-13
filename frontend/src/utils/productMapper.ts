/**
 * Map live backend products to frontend Product shape for ProductCard.
 */
import { LiveProduct } from '../services/api';
import { Product } from '../data/mockData';

export function liveProductToCard(p: LiveProduct): Product {
  const priceVal = p.price_value ?? (parseFloat(String(p.price).replace(/[^0-9.]/g, '')) || 0);
  const discount = 0;
  const originalPrice = priceVal;

  return {
    id: p.product_id,
    name: p.product_name || p.title || 'Unknown Product',
    category: p.category || 'General',
    price: Math.round(priceVal * 83),
    originalPrice: Math.round(originalPrice * 83),
    discount,
    rating: p.rating ?? 0,
    reviewCount: parseInt(p.rating_count || '0', 10) || p.stock || 0,
    image: p.thumbnail || 'https://via.placeholder.com/400x300?text=Product',
    badge: p.ai_match && p.ai_match >= 85 ? 'AI Choice' : undefined,
    inStock: (p.stock ?? 1) > 0,
    aiScore: Math.round(p.ai_match ?? (p.similarity_score ?? 0.5) * 100),
    pros: [],
    cons: [],
    features: {},
    description: p.description || '',
    brand: p.brand || '',
    sentimentScore: Math.round((p.rating ?? 0) / 5 * 100),
  };
}
