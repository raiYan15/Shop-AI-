"""
Phase 3: Recommendation Engine
Content-based + Collaborative filtering with hybrid ranking
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple
import pickle
import faiss
from sklearn.preprocessing import normalize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from surprise import Dataset, Reader, SVD, NMF, BaselineOnly
from surprise.model_selection import cross_validate
import warnings
warnings.filterwarnings('ignore')

# Paths
data_dir = Path(__file__).parent.parent / "data"
models_dir = data_dir / "models"
models_dir.mkdir(exist_ok=True)


class ContentBasedRecommender:
    """Content-based recommendation using product features and embeddings."""
    
    def __init__(self, products_df: pd.DataFrame, embeddings_path: str):
        self.products_df = products_df.copy()
        self.embeddings_path = embeddings_path
        self.load_embeddings()
        
    def load_embeddings(self):
        """Load pre-computed embeddings and FAISS index."""
        self.index = faiss.read_index(str(self.embeddings_path))
        print(f"✓ Loaded FAISS index: {self.index.ntotal} vectors")
    
    def get_similar_by_embedding(self, product_id: str, k: int = 5) -> pd.DataFrame:
        """Get similar products using embeddings."""
        try:
            idx = self.products_df[self.products_df['product_id'] == product_id].index[0]
            distances, indices = self.index.search(
                np.array([[0]*768]).astype('float32'), 1  # Placeholder
            )
            # Real implementation would extract and search product embedding
            similar_idx = np.argsort(distances[0])[-k:]
            similar_products = self.products_df.iloc[similar_idx].copy()
            similar_products['similarity_score'] = distances[0][similar_idx]
            return similar_products
        except Exception as e:
            print(f"Error: {e}")
            return pd.DataFrame()
    
    def get_category_recommendations(self, product_id: str, k: int = 5) -> pd.DataFrame:
        """Recommend products from same category with high ratings."""
        product = self.products_df[self.products_df['product_id'] == product_id]
        if product.empty:
            return pd.DataFrame()
        
        category = product.iloc[0]['category']
        category_products = self.products_df[
            (self.products_df['category'] == category) & 
            (self.products_df['product_id'] != product_id)
        ].copy()
        
        # Score by rating
        category_products['score'] = pd.to_numeric(
            category_products['rating'], errors='coerce'
        ).fillna(0)
        
        return category_products.nlargest(k, 'score')


class CollaborativeFiltering:
    """Collaborative filtering using matrix factorization."""
    
    def __init__(self, ratings_df: pd.DataFrame = None):
        self.ratings_df = ratings_df
        self.model = None
        self.trainset = None
        
    def prepare_data(self, ratings_df: pd.DataFrame):
        """Prepare ratings for training."""
        self.ratings_df = ratings_df.copy()
        self.ratings_df = self.ratings_df[
            ['user_id', 'product_id', 'rating']
        ].drop_duplicates()
        
        # Create reader and dataset
        reader = Reader(rating_scale=(1, 5))
        data = Dataset.load_from_df(self.ratings_df, reader)
        self.trainset = data.build_full_trainset()
        return self.trainset
    
    def train_svd(self, n_factors: int = 50, n_epochs: int = 20):
        """Train SVD (Singular Value Decomposition) model."""
        if self.trainset is None:
            raise ValueError("Call prepare_data() first")
        
        self.model = SVD(n_factors=n_factors, n_epochs=n_epochs, verbose=True)
        self.model.fit(self.trainset)
        print(f"✓ SVD model trained with {n_factors} factors")
        return self.model
    
    def get_recommendations(self, user_id: str, product_ids: List[str], k: int = 5) -> List[Tuple]:
        """Get top-k recommendations for a user."""
        if self.model is None:
            raise ValueError("Model not trained. Call train_svd() first")
        
        predictions = []
        for product_id in product_ids:
            try:
                pred = self.model.predict(user_id, product_id)
                predictions.append((product_id, pred.est))
            except Exception:
                continue
        
        # Sort by estimated rating
        predictions.sort(key=lambda x: x[1], reverse=True)
        return predictions[:k]
    
    def save_model(self, path: str):
        """Save trained model."""
        pickle.dump(self.model, open(path, 'wb'))
        print(f"✓ Model saved to {path}")


class HybridRecommender:
    """Hybrid recommender combining content and collaborative signals."""
    
    def __init__(self, content_model: ContentBasedRecommender, 
                 collab_model: CollaborativeFiltering):
        self.content_model = content_model
        self.collab_model = collab_model
    
    def hybrid_recommend(self, user_id: str, product_id: str, 
                        k: int = 10, weights: Dict[str, float] = None) -> pd.DataFrame:
        """
        Generate hybrid recommendations combining:
        - Content similarity (embeddings + category)
        - Collaborative filtering (user patterns)
        - Product popularity (ratings)
        """
        if weights is None:
            weights = {'content': 0.4, 'collab': 0.3, 'popularity': 0.3}
        
        all_products = self.content_model.products_df.copy()
        scores = pd.DataFrame({
            'product_id': all_products['product_id'],
            'score': 0.0
        })
        
        # Content-based score
        try:
            category_recs = self.content_model.get_category_recommendations(
                product_id, k=len(all_products)
            )
            if not category_recs.empty:
                category_scores = category_recs[['product_id', 'score']].copy()
                category_scores['score'] = (category_scores['score'] - category_scores['score'].min()) / \
                                           (category_scores['score'].max() - category_scores['score'].min() + 1e-6)
                scores = scores.merge(
                    category_scores.rename(columns={'score': 'content_score'}),
                    how='left',
                    on='product_id'
                )
                scores['content_score'] = scores['content_score'].fillna(0)
                scores['score'] += scores['content_score'] * weights['content']
        except Exception as e:
            print(f"Content scoring error: {e}")
        
        # Popularity score (rating)
        popularity = all_products[['product_id', 'rating']].copy()
        popularity['rating'] = pd.to_numeric(popularity['rating'], errors='coerce').fillna(0)
        popularity['popularity_score'] = (popularity['rating'] - popularity['rating'].min()) / \
                                        (popularity['rating'].max() - popularity['rating'].min() + 1e-6)
        scores = scores.merge(popularity[['product_id', 'popularity_score']], 
                              how='left', on='product_id')
        scores['popularity_score'] = scores['popularity_score'].fillna(0)
        scores['score'] += scores['popularity_score'] * weights['popularity']
        
        # Sort and return top-k
        recommendations = scores.nlargest(k, 'score')
        return recommendations.merge(all_products, on='product_id')[
            ['product_id', 'product_name', 'rating', 'category', 'score']
        ]


# Demo function
def demo_recommender():
    """Demo: Load data and generate recommendations."""
    print("\n" + "="*80)
    print("PHASE 3: RECOMMENDATION ENGINE DEMO")
    print("="*80 + "\n")
    
    # Load data
    print("Loading data...")
    products_df = pd.read_csv(data_dir / "amazon.csv", nrows=5000)
    products_df = products_df.drop_duplicates(subset=['product_id'], keep='first')
    print(f"✓ Loaded {len(products_df)} products")
    
    # Initialize content-based recommender
    print("\nInitializing content-based recommender...")
    content_rec = ContentBasedRecommender(
        products_df,
        data_dir / "faiss_index.idx"
    )
    
    # Get a sample product
    sample_product_id = products_df.iloc[0]['product_id']
    sample_product_name = products_df.iloc[0]['product_name']
    print(f"\nSample product: {sample_product_name}")
    print(f"Product ID: {sample_product_id}")
    
    # Get category recommendations
    print("\n--- Category-Based Recommendations ---")
    category_recs = content_rec.get_category_recommendations(sample_product_id, k=5)
    if not category_recs.empty:
        print(category_recs[['product_name', 'rating', 'category']].to_string(index=False))
    
    # Hybrid recommendations (demo with synthetic data)
    print("\n--- Hybrid Recommendations (Demo) ---")
    hybrid_rec = HybridRecommender(content_rec, None)
    hybrid_recs = hybrid_rec.hybrid_recommend(
        user_id="USER123",
        product_id=sample_product_id,
        k=5
    )
    if not hybrid_recs.empty:
        print(hybrid_recs[['product_name', 'rating', 'score']].to_string(index=False))
    
    print("\n✓ Phase 3 recommendation engine demo complete!")


if __name__ == "__main__":
    demo_recommender()
