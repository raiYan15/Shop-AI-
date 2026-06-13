"""
Phase 4: Review Intelligence System
BERT sentiment analysis + review summarization
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple
import re
from collections import Counter

try:
    from transformers import pipeline
    from summarizer import Summarizer
except ImportError:
    pass

# Paths
data_dir = Path(__file__).parent.parent / "data"
models_dir = data_dir / "models"
models_dir.mkdir(exist_ok=True)


class SentimentAnalyzer:
    """BERT-based sentiment analysis for product reviews."""
    
    def __init__(self, model_name: str = "distilbert-base-uncased-finetuned-sst-2-english"):
        """Initialize sentiment analysis pipeline."""
        try:
            self.classifier = pipeline("sentiment-classification", model=model_name)
            print(f"✓ Sentiment classifier loaded: {model_name}")
        except Exception as e:
            print(f"⚠ Could not load sentiment model: {e}")
            print("  Using fallback keyword-based analyzer...")
            self.classifier = None
    
    def analyze(self, text: str) -> Dict[str, float]:
        """
        Analyze sentiment of text.
        Returns: {'label': 'POSITIVE'/'NEGATIVE'/'NEUTRAL', 'score': 0-1}
        """
        if not text or len(text.strip()) < 3:
            return {'label': 'NEUTRAL', 'score': 0.5}
        
        if self.classifier:
            try:
                # Truncate long text
                text = text[:512]
                result = self.classifier(text)[0]
                return {
                    'label': result['label'],
                    'score': result['score']
                }
            except Exception as e:
                print(f"Error in sentiment analysis: {e}")
        
        # Fallback: keyword-based sentiment
        return self._keyword_sentiment(text)
    
    def _keyword_sentiment(self, text: str) -> Dict[str, float]:
        """Fallback keyword-based sentiment analysis."""
        positive_words = {'good', 'great', 'excellent', 'amazing', 'love', 'best', 
                         'fantastic', 'perfect', 'awesome', 'wonderful', 'quality'}
        negative_words = {'bad', 'poor', 'terrible', 'worst', 'hate', 'horrible',
                         'awful', 'broken', 'issue', 'problem', 'disappointed'}
        
        text_lower = text.lower()
        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)
        
        if pos_count > neg_count:
            return {'label': 'POSITIVE', 'score': min(0.9, 0.5 + pos_count * 0.1)}
        elif neg_count > pos_count:
            return {'label': 'NEGATIVE', 'score': min(0.9, 0.5 + neg_count * 0.1)}
        else:
            return {'label': 'NEUTRAL', 'score': 0.5}
    
    def batch_analyze(self, texts: List[str]) -> List[Dict]:
        """Analyze sentiment for multiple texts."""
        return [self.analyze(text) for text in texts]


class ReviewSummarizer:
    """Extract key insights from product reviews."""
    
    def __init__(self):
        """Initialize review summarization components."""
        self.sentiment_analyzer = SentimentAnalyzer()
    
    def extract_key_phrases(self, text: str, top_n: int = 5) -> List[str]:
        """Extract noun phrases from review text."""
        # Simple pattern matching for key features
        patterns = [
            r'(?:very\s+)?(\w+(?:\s+\w+)?)\s+(?:is|are|was|were)',
            r'(?:great|good|bad|poor)\s+(\w+(?:\s+\w+)?)',
            r'(?:excellent|amazing|terrible)\s+(\w+(?:\s+\w+)?)',
        ]
        
        phrases = []
        text_lower = text.lower()
        
        for pattern in patterns:
            matches = re.findall(pattern, text_lower)
            phrases.extend([m.strip() for m in matches if len(m.strip()) > 2])
        
        # Count and return top phrases
        phrase_counts = Counter(phrases)
        return [phrase for phrase, _ in phrase_counts.most_common(top_n)]
    
    def summarize_reviews(self, reviews: List[str], k: int = 3) -> Dict[str, any]:
        """
        Summarize multiple reviews into key insights.
        
        Returns:
            {
                'positive_themes': [],
                'negative_themes': [],
                'overall_sentiment': str,
                'sentiment_distribution': {POSITIVE, NEGATIVE, NEUTRAL},
                'key_strengths': [],
                'key_weaknesses': []
            }
        """
        if not reviews:
            return {}
        
        # Analyze sentiments
        sentiments = self.sentiment_analyzer.batch_analyze(reviews)
        
        # Extract themes
        all_phrases = []
        positive_phrases = []
        negative_phrases = []
        
        for review, sentiment in zip(reviews, sentiments):
            phrases = self.extract_key_phrases(review, top_n=3)
            all_phrases.extend(phrases)
            
            if sentiment['label'] == 'POSITIVE':
                positive_phrases.extend(phrases)
            elif sentiment['label'] == 'NEGATIVE':
                negative_phrases.extend(phrases)
        
        # Sentiment distribution
        sentiment_dist = Counter([s['label'] for s in sentiments])
        
        # Determine overall sentiment
        if sentiment_dist.get('POSITIVE', 0) > len(reviews) * 0.6:
            overall = 'HIGHLY_POSITIVE'
        elif sentiment_dist.get('POSITIVE', 0) > len(reviews) * 0.4:
            overall = 'POSITIVE'
        elif sentiment_dist.get('NEGATIVE', 0) > len(reviews) * 0.6:
            overall = 'HIGHLY_NEGATIVE'
        elif sentiment_dist.get('NEGATIVE', 0) > len(reviews) * 0.4:
            overall = 'NEGATIVE'
        else:
            overall = 'NEUTRAL'
        
        return {
            'overall_sentiment': overall,
            'sentiment_distribution': dict(sentiment_dist),
            'key_strengths': [phrase for phrase, _ in Counter(positive_phrases).most_common(k)],
            'key_weaknesses': [phrase for phrase, _ in Counter(negative_phrases).most_common(k)],
            'total_reviews_analyzed': len(reviews),
            'average_sentiment_score': np.mean([s['score'] for s in sentiments])
        }


class ReviewIntelligence:
    """Complete review intelligence pipeline."""
    
    def __init__(self):
        self.sentiment_analyzer = SentimentAnalyzer()
        self.summarizer = ReviewSummarizer()
    
    def analyze_product_reviews(self, reviews_df: pd.DataFrame, product_id: str) -> Dict:
        """Analyze all reviews for a product."""
        product_reviews = reviews_df[reviews_df['product_id'] == product_id]
        
        if product_reviews.empty:
            return {'error': 'No reviews found for product'}
        
        review_texts = product_reviews['review_content'].fillna('').astype(str).tolist()
        
        # Get summary
        summary = self.summarizer.summarize_reviews(review_texts, k=3)
        
        # Add individual sentiment analysis
        individual_sentiments = []
        for _, review in product_reviews.iterrows():
            text = review.get('review_content', '')
            sentiment = self.sentiment_analyzer.analyze(text)
            individual_sentiments.append({
                'review_id': review.get('review_id', 'unknown'),
                'sentiment': sentiment['label'],
                'confidence': sentiment['score']
            })
        
        summary['individual_reviews'] = individual_sentiments
        summary['review_count'] = len(review_texts)
        
        return summary


# Demo function
def demo_review_intelligence():
    """Demo: Analyze product reviews."""
    print("\n" + "="*80)
    print("PHASE 4: REVIEW INTELLIGENCE SYSTEM DEMO")
    print("="*80 + "\n")
    
    # Load data
    print("Loading data...")
    try:
        df = pd.read_csv(data_dir / "amazon.csv", nrows=5000)
        df = df.drop_duplicates(subset=['product_id'], keep='first')
        print(f"✓ Loaded {len(df)} products\n")
        
        # Get a product with reviews
        sample_product_id = df.iloc[0]['product_id']
        sample_product_name = df.iloc[0]['product_name']
        
        print(f"Sample Product: {sample_product_name[:80]}...")
        print(f"Product ID: {sample_product_id}\n")
        
        # Initialize review intelligence
        review_intel = ReviewIntelligence()
        
        # Simulate sample reviews (from product data)
        sample_reviews = [
            "Great product, works as expected. Excellent quality and fast delivery.",
            "Good value for money. Highly recommended for this price range.",
            "Poor quality, broke after a week. Not worth the money. Terrible customer service.",
            "Amazing build quality. Battery life is exceptional. Love it!",
            "Average product. Nothing special. Works but has some issues."
        ]
        
        print("--- Analyzing Sample Reviews ---")
        
        # Analyze individual reviews
        print("\nIndividual Review Sentiments:")
        sentiment_analyzer = SentimentAnalyzer()
        for i, review in enumerate(sample_reviews, 1):
            sentiment = sentiment_analyzer.analyze(review)
            print(f"{i}. {review[:50]}...")
            print(f"   Sentiment: {sentiment['label']} (Confidence: {sentiment['score']:.2f})\n")
        
        # Summarize reviews
        print("--- Review Summary ---")
        summary = ReviewSummarizer().summarize_reviews(sample_reviews, k=3)
        
        print(f"Overall Sentiment: {summary['overall_sentiment']}")
        print(f"Average Sentiment Score: {summary['average_sentiment_score']:.2f}")
        print(f"Sentiment Distribution: {summary['sentiment_distribution']}")
        print(f"\nKey Strengths: {', '.join(summary['key_strengths']) if summary['key_strengths'] else 'N/A'}")
        print(f"Key Weaknesses: {', '.join(summary['key_weaknesses']) if summary['key_weaknesses'] else 'N/A'}")
        
    except Exception as e:
        print(f"Error in demo: {e}")
    
    print("\n✓ Phase 4 review intelligence demo complete!")


if __name__ == "__main__":
    demo_review_intelligence()
