"""
Phase 5: RAG (Retrieval Augmented Generation) + LLM Shopping Copilot
Combines semantic search + LLM for intelligent shopping assistance
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional
import faiss
import pickle
from sentence_transformers import SentenceTransformer
from sklearn.preprocessing import normalize

# Paths
data_dir = Path(__file__).parent.parent / "data"
models_dir = data_dir / "models"
models_dir.mkdir(exist_ok=True)


class SimpleRAG:
    """
    Retrieval Augmented Generation (RAG) pipeline.
    Retrieves relevant products and passes context to LLM-like generator.
    """
    
    def __init__(self, index_path: str, idmap_path: str, products_df: pd.DataFrame):
        """Initialize RAG with FAISS index and product data."""
        self.index = faiss.read_index(index_path)
        with open(idmap_path, 'rb') as f:
            self.product_ids = pickle.load(f)
        self.products_df = products_df
        self.model = SentenceTransformer('all-mpnet-base-v2')
        print(f"✓ RAG initialized: {len(products_df)} products indexed")
    
    def retrieve_context(self, query: str, k: int = 5) -> List[Dict]:
        """
        Retrieve top-k products relevant to query.
        Returns context for LLM augmentation.
        """
        # Encode query
        query_embedding = self.model.encode(query, convert_to_numpy=True).astype('float32')
        query_embedding = normalize([query_embedding])[0]
        
        # Search
        distances, indices = self.index.search(np.array([query_embedding]), k)
        
        # Build context
        context = []
        for i, idx in enumerate(indices[0]):
            product_id = self.product_ids[idx]
            product = self.products_df[self.products_df['product_id'] == product_id].iloc[0]
            
            context.append({
                'product_id': product_id,
                'product_name': product.get('product_name', 'N/A'),
                'price': product.get('discounted_price', 'N/A'),
                'rating': product.get('rating', 'N/A'),
                'category': product.get('category', 'N/A'),
                'description': product.get('about_product', '')[:200],
                'relevance_score': distances[0][i]
            })
        
        return context
    
    def build_augmented_prompt(self, user_query: str, context: List[Dict]) -> str:
        """Build prompt with retrieved context for LLM."""
        context_text = "\n".join([
            f"- {p['product_name']} | Price: {p['price']} | Rating: {p['rating']} | Relevance: {p['relevance_score']:.2f}"
            for p in context
        ])
        
        prompt = f"""You are a helpful shopping assistant. Based on the user query and retrieved products, 
provide personalized shopping advice and recommendations.

User Query: {user_query}

Retrieved Products:
{context_text}

Provide:
1. Which product best matches the query
2. Why it's a good match (features, price, ratings)
3. Alternative recommendations if applicable
4. Key considerations for the user

Response:"""
        
        return prompt


class ShoppingCopilot:
    """
    AI Shopping Copilot combining RAG with LLM-like responses.
    Provides product recommendations, comparisons, and shopping advice.
    """
    
    def __init__(self, rag: SimpleRAG):
        self.rag = rag
    
    def compare_products(self, product_ids: List[str]) -> Dict:
        """Compare multiple products side-by-side."""
        products = []
        for pid in product_ids:
            product = self.rag.products_df[
                self.rag.products_df['product_id'] == pid
            ]
            if not product.empty:
                p = product.iloc[0]
                products.append({
                    'id': pid,
                    'name': p.get('product_name', 'N/A'),
                    'price': p.get('discounted_price', 'N/A'),
                    'rating': p.get('rating', 'N/A'),
                    'category': p.get('category', 'N/A'),
                    'features': p.get('about_product', '')[:300]
                })
        
        return {
            'comparison': products,
            'recommendation': self._generate_comparison_advice(products)
        }
    
    def _generate_comparison_advice(self, products: List[Dict]) -> str:
        """Generate recommendation based on product comparison."""
        if len(products) < 2:
            return "Need at least 2 products to compare."
        
        # Simple heuristic: highest rating and reasonable price
        best_value = max(products, key=lambda p: float(str(p['rating']).replace(',', '')) 
                        if isinstance(p['rating'], (str, int, float)) else 0)
        
        return f"Best overall choice: {best_value['name']} with {best_value['rating']} rating"
    
    def search_with_advice(self, query: str, k: int = 5) -> Dict:
        """Search and provide AI-assisted shopping advice."""
        # Retrieve context
        context = self.rag.retrieve_context(query, k)
        
        if not context:
            return {'error': 'No products found'}
        
        # Generate advice prompt
        prompt = self.rag.build_augmented_prompt(query, context)
        
        # Generate response (simulated LLM response)
        advice = self._generate_shopping_advice(query, context)
        
        return {
            'query': query,
            'advice': advice,
            'recommended_products': context[:3],
            'similar_alternatives': context[3:] if len(context) > 3 else [],
            'prompt_for_llm': prompt
        }
    
    def _generate_shopping_advice(self, query: str, context: List[Dict]) -> str:
        """Generate shopping advice based on retrieved products."""
        top_product = context[0]
        
        advice_parts = [
            f"Based on your search for '{query}', I recommend:",
            f"\n✓ Top Pick: {top_product['product_name']}",
            f"  - Price: {top_product['price']}",
            f"  - Rating: {top_product['rating']}/5",
            f"  - Why: Highly relevant and well-rated option"
        ]
        
        if len(context) > 1:
            advice_parts.append(f"\n✓ Alternative Options:")
            for alt in context[1:3]:
                advice_parts.append(f"  - {alt['product_name']} ({alt['price']})")
        
        advice_parts.append("\nConsiderations:")
        advice_parts.append("- Compare prices across similar products")
        advice_parts.append("- Check ratings and customer reviews")
        advice_parts.append("- Verify specifications match your needs")
        
        return "\n".join(advice_parts)
    
    def budget_recommendation(self, category: str, max_price: str, preference: str = "best_value") -> Dict:
        """Recommend products within budget."""
        # Parse max price
        try:
            price_str = max_price.replace('₹', '').replace(',', '').strip()
            max_price_num = float(price_str)
        except:
            max_price_num = 50000  # Default
        
        # Filter products
        products = self.rag.products_df.copy()
        
        # Filter by category if specified
        if category != "any":
            products = products[products['category'].str.contains(category, na=False, case=False)]
        
        # Extract numeric price from discount price
        try:
            products['price_numeric'] = products['discounted_price'].str.replace('₹', '').str.replace(',', '').astype(float)
            products = products[products['price_numeric'] <= max_price_num]
        except:
            pass
        
        if products.empty:
            return {'error': f'No products found in {category} under ₹{max_price_num}'}
        
        # Score by rating
        products['rating_numeric'] = pd.to_numeric(products['rating'], errors='coerce').fillna(0)
        
        if preference == "best_value":
            top_products = products.nlargest(5, 'rating_numeric')
        elif preference == "cheapest":
            top_products = products.nsmallest(5, 'price_numeric')
        else:
            top_products = products.head(5)
        
        return {
            'query': f'{category} under ₹{max_price_num}',
            'results': top_products[['product_name', 'discounted_price', 'rating', 'category']].to_dict('records')
        }


# Demo function
def demo_shopping_copilot():
    """Demo: RAG-based shopping copilot."""
    print("\n" + "="*80)
    print("PHASE 5: RAG + LLM SHOPPING COPILOT DEMO")
    print("="*80 + "\n")
    
    # Load data
    print("Loading data...")
    products_df = pd.read_csv(data_dir / "amazon.csv", nrows=5000)
    products_df = products_df.drop_duplicates(subset=['product_id'], keep='first')
    print(f"✓ Loaded {len(products_df)} products\n")
    
    # Initialize RAG
    rag = SimpleRAG(
        str(data_dir / "faiss_index.idx"),
        str(data_dir / "id_map.pkl"),
        products_df
    )
    
    # Initialize Copilot
    copilot = ShoppingCopilot(rag)
    
    # Demo queries
    demo_queries = [
        "I need a good laptop under 70000 for coding and machine learning",
        "Best USB cables for fast charging",
        "Budget-friendly wireless headphones with good sound"
    ]
    
    print("--- Semantic Search + Shopping Advice ---\n")
    for query in demo_queries:
        print(f"Query: {query}")
        result = copilot.search_with_advice(query, k=3)
        print(f"\nAI Assistant Advice:")
        print(result['advice'])
        print("\n" + "-"*80 + "\n")
    
    # Budget recommendation
    print("--- Budget-Based Recommendation ---")
    budget_result = copilot.budget_recommendation(
        category="USB",
        max_price="₹500",
        preference="best_value"
    )
    
    if 'results' in budget_result:
        print(f"Query: {budget_result['query']}")
        for i, p in enumerate(budget_result['results'], 1):
            print(f"{i}. {p['product_name'][:60]} - {p['discounted_price']} (Rating: {p['rating']})")
    else:
        print(f"Query: {budget_result.get('query', 'N/A')}")
        print(budget_result.get('error', 'N/A'))
    
    print("\n✓ Phase 5 RAG + LLM Copilot demo complete!")


if __name__ == "__main__":
    demo_shopping_copilot()
