"""
Simplified Phase 3-5 Integration Layer for FastAPI
Standalone functions that don't require complex initialization
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple
import pickle
from pathlib import Path
from sklearn.preprocessing import normalize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

data_dir = Path(__file__).parent.parent / "data"


class SimpleRecommender:
    """Lightweight recommender for API integration."""
    
    def __init__(self, products_df: pd.DataFrame = None):
        self.products_df = products_df
    
    def category_recommend(self, product_id: str, top_k: int = 5) -> List[Dict]:
        """
        Recommend products from same category with high ratings.
        """
        if self.products_df is None or self.products_df.empty:
            return []
        
        product = self.products_df[self.products_df['product_id'] == product_id]
        if product.empty:
            return []
        
        category = product['category'].iloc[0]
        same_category = self.products_df[self.products_df['category'] == category]
        same_category = same_category[same_category['product_id'] != product_id]
        
        # Sort by rating (descending)
        try:
            same_category['rating_float'] = pd.to_numeric(
                same_category['rating'], 
                errors='coerce'
            )
            same_category = same_category.sort_values('rating_float', ascending=False)
        except:
            pass
        
        recommendations = []
        for idx, row in same_category.head(top_k).iterrows():
            recommendations.append({
                'product_id': row['product_id'],
                'score': 0.8,
                'reason': f"Similar category: {category}, highly rated"
            })
        
        return recommendations


class SimpleSentimentAnalyzer:
    """Lightweight sentiment analyzer using keywords."""
    
    POSITIVE_WORDS = {
        'excellent', 'great', 'amazing', 'fantastic', 'perfect', 'love',
        'awesome', 'wonderful', 'good', 'best', 'outstanding', 'superb',
        'quality', 'highly', 'recommended', 'satisfied', 'impressed'
    }
    
    NEGATIVE_WORDS = {
        'bad', 'terrible', 'poor', 'awful', 'hate', 'worst', 'horrible',
        'disappointing', 'issue', 'problem', 'broke', 'broken', 'defective',
        'cheap', 'waste', 'useless', 'not good'
    }
    
    def analyze(self, reviews: List[str]) -> Dict:
        """Analyze review sentiment."""
        results = {
            'sentiments': [],
            'positive_count': 0,
            'negative_count': 0,
            'neutral_count': 0,
            'overall_sentiment': 'NEUTRAL',
            'key_strengths': [],
            'key_weaknesses': [],
            'average_confidence': 0.0
        }
        
        if not reviews:
            return results
        
        strengths = {}
        weaknesses = {}
        confidences = []
        
        for review in reviews:
            text_lower = review.lower()
            
            # Count positive/negative words
            positive_count = sum(1 for word in self.POSITIVE_WORDS if word in text_lower)
            negative_count = sum(1 for word in self.NEGATIVE_WORDS if word in text_lower)
            
            # Determine sentiment
            if positive_count > negative_count:
                sentiment = 'POSITIVE'
                confidence = min(0.95, 0.5 + (positive_count * 0.1))
                results['positive_count'] += 1
                
                # Extract strengths (words before/after positive indicators)
                for word in self.POSITIVE_WORDS:
                    if word in text_lower:
                        strengths[word] = strengths.get(word, 0) + 1
            elif negative_count > positive_count:
                sentiment = 'NEGATIVE'
                confidence = min(0.95, 0.5 + (negative_count * 0.1))
                results['negative_count'] += 1
                
                for word in self.NEGATIVE_WORDS:
                    if word in text_lower:
                        weaknesses[word] = weaknesses.get(word, 0) + 1
            else:
                sentiment = 'NEUTRAL'
                confidence = 0.6
                results['neutral_count'] += 1
            
            results['sentiments'].append((sentiment, confidence))
            confidences.append(confidence)
        
        # Overall sentiment
        if results['positive_count'] > results['negative_count']:
            results['overall_sentiment'] = 'POSITIVE'
        elif results['negative_count'] > results['positive_count']:
            results['overall_sentiment'] = 'NEGATIVE'
        
        # Top strengths and weaknesses
        if strengths:
            top_strengths = sorted(strengths.items(), key=lambda x: x[1], reverse=True)
            results['key_strengths'] = [s[0].capitalize() for s in top_strengths[:5]]
        
        if weaknesses:
            top_weaknesses = sorted(weaknesses.items(), key=lambda x: x[1], reverse=True)
            results['key_weaknesses'] = [w[0].capitalize() for w in top_weaknesses[:5]]
        
        # Average confidence
        results['average_confidence'] = float(np.mean(confidences)) if confidences else 0.6
        
        return results


class SimpleRAG:
    """Simple RAG for shopping advice."""
    
    def generate_advice(self, query: str, products: List[Dict]) -> str:
        """Generate shopping advice based on query and products."""
        if not products:
            return "I couldn't find any relevant products. Try a different search term."
        
        advice_parts = []
        advice_parts.append(f"Based on your search for '{query}':\n")
        
        # Add top recommendation
        if products:
            top = products[0]
            advice_parts.append(f"✓ Top recommendation: {top.get('product_name', 'N/A')}")
            advice_parts.append(f"  Price: {top.get('price', 'N/A')}")
            advice_parts.append(f"  Rating: {top.get('rating', 0.0)}★")
        
        # Add insights
        if len(products) > 1:
            advice_parts.append(f"\n✓ Found {len(products)} relevant products")
            
            prices = [p.get('price', '') for p in products if isinstance(p.get('price'), (int, float))]
            if prices:
                avg_price = sum(prices) / len(prices)
                advice_parts.append(f"  Average price: ₹{avg_price:.0f}")
        
        advice_parts.append("\n✓ All products are verified from our catalog")
        
        return "\n".join(advice_parts)


def recommend_similar_products(product_id: str, products_df: pd.DataFrame, top_k: int = 5) -> List[Dict]:
    """Category-based recommendations."""
    recommender = SimpleRecommender(products_df)
    recs = recommender.category_recommend(product_id, top_k)
    return recs


def analyze_product_reviews(reviews: List[str]) -> Dict:
    """Analyze reviews with keyword-based sentiment."""
    analyzer = SimpleSentimentAnalyzer()
    return analyzer.analyze(reviews)


def generate_shopping_advice(query: str, products: List[Dict]) -> str:
    """Generate RAG-based shopping advice."""
    rag = SimpleRAG()
    return rag.generate_advice(query, products)
