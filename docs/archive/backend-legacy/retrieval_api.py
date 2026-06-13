"""
ShopMind AI - Integrated FastAPI Backend
Semantic search + recommendations + review intelligence + RAG copilot
"""

import os
import pickle
import asyncio
import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from sklearn.preprocessing import normalize
import faiss

# Import Phase 3-5 modules
import sys
sys.path.insert(0, str(Path(__file__).parent))
from phase3_5_integration import (
    recommend_similar_products,
    analyze_product_reviews,
    generate_shopping_advice
)

# Initialize FastAPI app
app = FastAPI(
    title="ShopMind AI - Retrieval API",
    description="Semantic search and product retrieval engine",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for models and data
embedding_model = None
faiss_index = None
product_ids = None
products_df = None
data_dir = Path(__file__).parent.parent / "data"


class SearchQuery(BaseModel):
    query: str
    top_k: int = 5


class SearchResult(BaseModel):
    product_id: str
    product_name: str
    category: str
    price: str
    rating: float
    rating_count: str
    similarity_score: float


class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]
    count: int


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _format_live_product(row: pd.Series) -> Dict[str, Any]:
    rating = _safe_float(row.get('rating', 0.0), 0.0)
    ai_match = round((rating / 5) * 100, 1) if rating > 0 else 0.0
    return {
        "product_id": str(row.get('product_id', '')),
        "product_name": str(row.get('product_name', 'N/A')),
        "category": str(row.get('category', 'N/A')).lower(),
        "price": str(row.get('discounted_price', 'N/A')),
        "rating": rating,
        "rating_count": str(row.get('rating_count', '0')),
        "description": str(row.get('about_product', '')),
        "brand": str(row.get('brand', 'ShopMind')),
        "ai_match": ai_match,
        "source": "csv",
    }


def _products_snapshot(
    page: int,
    limit: int,
    category: Optional[str],
    sort: str,
) -> Dict[str, Any]:
    if products_df is None:
        raise HTTPException(status_code=503, detail="Data not loaded")

    df = products_df
    if category:
        df = df[df['category'].astype(str).str.lower() == category.lower()]

    sort_col = {
        "updated_at": None,
        "rating": "rating",
        "price": "discounted_price",
        "title": "product_name",
    }.get(sort, None)

    if sort_col and sort_col in df.columns:
        ascending = sort == "title"
        if sort_col in ("rating", "discounted_price"):
            tmp = df.copy()
            tmp[sort_col] = pd.to_numeric(tmp[sort_col], errors='coerce')
            df = tmp.sort_values(by=sort_col, ascending=ascending, na_position='last')
        else:
            df = df.sort_values(by=sort_col, ascending=ascending)

    total = int(len(df))
    start = (page - 1) * limit
    end = start + limit
    page_df = df.iloc[start:end]

    products = [_format_live_product(row) for _, row in page_df.iterrows()]
    pages = max(1, (total + limit - 1) // limit)

    return {
        "products": products,
        "page": page,
        "limit": limit,
        "total": total,
        "pages": pages,
        "data_source": "csv",
    }


def load_models():
    """Load embedding model, FAISS index, and product data."""
    global embedding_model, faiss_index, product_ids, products_df
    
    try:
        # Load embedding model
        embedding_model = SentenceTransformer('all-mpnet-base-v2')
        
        # Load FAISS index
        index_path = data_dir / "faiss_index.idx"
        faiss_index = faiss.read_index(str(index_path))
        
        # Load product ID mapping
        idmap_path = data_dir / "id_map.pkl"
        with open(idmap_path, 'rb') as f:
            product_ids = pickle.load(f)
        
        # Load products CSV
        csv_path = data_dir / "amazon.csv"
        products_df = pd.read_csv(csv_path, nrows=5000)
        products_df = products_df.drop_duplicates(subset=['product_id'], keep='first')
        
        print(f"✓ Models loaded successfully")
        print(f"  - Embedding model: {embedding_model.get_sentence_embedding_dimension()}-dim")
        print(f"  - FAISS index: {faiss_index.ntotal} vectors")
        print(f"  - Products: {len(products_df)} unique items")
        print(f"  - Phase 3: Category-based recommender ready")
        print(f"  - Phase 4: Sentiment analyzer ready")
        print(f"  - Phase 5: RAG copilot ready")
    except Exception as e:
        print(f"✗ Failed to load models: {e}")
        raise


@app.on_event("startup")
async def startup_event():
    """Load models on startup."""
    load_models()


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "models_loaded": embedding_model is not None and faiss_index is not None
    }


@app.post("/search", response_model=SearchResponse, tags=["Search"])
async def semantic_search(request: SearchQuery):
    """
    Perform semantic search on products.
    
    Args:
        query: Natural language search query
        top_k: Number of results to return (1-20)
    
    Returns:
        SearchResponse with top-k products and similarity scores
    """
    if not embedding_model or not faiss_index:
        raise HTTPException(status_code=503, detail="Models not loaded")
    
    # Validate top_k
    top_k = max(1, min(request.top_k, 20))
    
    try:
        # Encode query
        query_embedding = embedding_model.encode(
            request.query,
            convert_to_numpy=True
        ).astype('float32')
        query_embedding = normalize([query_embedding])[0]
        
        # Search FAISS index
        distances, indices = faiss_index.search(
            np.array([query_embedding]),
            k=top_k
        )
        
        # Retrieve and format results
        results = []
        for i, idx in enumerate(indices[0]):
            product_id = product_ids[idx]
            product = products_df[products_df['product_id'] == product_id].iloc[0]
            
            results.append(SearchResult(
                product_id=str(product_id),
                product_name=str(product.get('product_name', 'N/A')),
                category=str(product.get('category', 'N/A')),
                price=str(product.get('discounted_price', 'N/A')),
                rating=float(product.get('rating', 0.0)),
                rating_count=str(product.get('rating_count', '0')),
                similarity_score=float(distances[0][i])
            ))
        
        return SearchResponse(
            query=request.query,
            results=results,
            count=len(results)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.get("/product/{product_id}", tags=["Product"])
async def get_product(product_id: str):
    """
    Retrieve product details by ID.
    
    Args:
        product_id: Amazon product ID
    
    Returns:
        Product details
    """
    if products_df is None:
        raise HTTPException(status_code=503, detail="Data not loaded")
    
    product = products_df[products_df['product_id'] == product_id]
    if product.empty:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product = product.iloc[0]
    return {
        "product_id": product_id,
        "product_name": product.get('product_name', 'N/A'),
        "category": product.get('category', 'N/A'),
        "price": product.get('discounted_price', 'N/A'),
        "original_price": product.get('actual_price', 'N/A'),
        "rating": float(product.get('rating', 0.0)),
        "rating_count": product.get('rating_count', '0'),
        "description": product.get('about_product', 'N/A')
    }


@app.get("/products/live", tags=["Product"])
async def get_products_live(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=200),
    category: Optional[str] = None,
    sort: str = Query("updated_at", pattern="^(updated_at|rating|price|title)$"),
):
    payload = _products_snapshot(page=page, limit=limit, category=category, sort=sort)
    return {
        **payload,
        "realtime": True,
        "server_time": datetime.utcnow().isoformat(),
    }


@app.get("/products/stream", tags=["Product"])
async def stream_products_live(
    request: Request,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=200),
    category: Optional[str] = None,
    sort: str = Query("updated_at", pattern="^(updated_at|rating|price|title)$"),
    interval: float = Query(5.0, ge=1.0, le=30.0),
):

    async def event_generator():
        last_signature: Optional[str] = None

        while True:
            if await request.is_disconnected():
                break

            payload = _products_snapshot(page=page, limit=limit, category=category, sort=sort)
            enriched = {
                **payload,
                "realtime": True,
                "server_time": datetime.utcnow().isoformat(),
            }

            ids = [str(p.get("product_id", "")) for p in enriched.get("products", [])[:20]]
            signature = f"{enriched.get('data_source')}|{enriched.get('total')}|{','.join(ids)}"
            event_name = "update" if signature != last_signature else "heartbeat"
            last_signature = signature

            yield f"event: {event_name}\n"
            yield f"data: {json.dumps(enriched, default=str)}\n\n"
            await asyncio.sleep(interval)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/search-quick", tags=["Search"])
async def quick_search(
    q: str = Query(..., min_length=1, max_length=500),
    k: int = Query(5, ge=1, le=20)
):
    """
    Quick search endpoint with query parameters.
    
    Args:
        q: Search query
        k: Number of results
    
    Returns:
        JSON array of top-k products
    """
    request = SearchQuery(query=q, top_k=k)
    response = await semantic_search(request)
    return response


@app.get("/stats", tags=["Stats"])
async def get_stats():
    """Get index statistics."""
    if not faiss_index or products_df is None:
        raise HTTPException(status_code=503, detail="Data not loaded")
    
    try:
        avg_rating = 0
        if 'rating' in products_df.columns:
            # Convert to numeric, handling both string and numeric values
            ratings = pd.to_numeric(products_df['rating'], errors='coerce')
            avg_rating = float(ratings.mean())
    except Exception as e:
        avg_rating = 0
    
    return {
        "total_products": len(products_df),
        "index_vectors": faiss_index.ntotal,
        "embedding_dimension": faiss_index.d,
        "categories": len(products_df['category'].unique()) if 'category' in products_df.columns else 0,
        "avg_rating": avg_rating
    }


# ============= PHASE 3: Recommendations =============

class RecommendationRequest(BaseModel):
    product_id: str
    top_k: int = 5
    user_id: Optional[str] = None


class RecommendationItem(BaseModel):
    product_id: str
    product_name: str
    category: str
    price: str
    rating: float
    score: float
    reason: str


class RecommendationResponse(BaseModel):
    query_product_id: str
    recommendations: List[RecommendationItem]
    count: int
    timestamp: datetime


# Initialize Phase 3-5 modules
recommender = None
review_analyzer = None
copilot = None


@app.post("/recommend", response_model=RecommendationResponse, tags=["Recommendations"])
async def get_recommendations(request: RecommendationRequest):
    """
    Get personalized product recommendations.
    
    Phase 3: Category-based + popularity ranking
    
    Args:
        product_id: Product to get recommendations for
        top_k: Number of recommendations
        user_id: Optional user ID for future collaborative filtering
    
    Returns:
        RecommendationResponse with top-k recommended products
    """
    if products_df is None:
        raise HTTPException(status_code=503, detail="Data not loaded")
    
    try:
        # Get query product
        query_product = products_df[products_df['product_id'] == request.product_id]
        if query_product.empty:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Get recommendations using simple integration
        recs = recommend_similar_products(
            product_id=request.product_id,
            products_df=products_df,
            top_k=request.top_k
        )
        
        recommendations = []
        for rec in recs:
            prod = products_df[products_df['product_id'] == rec['product_id']]
            if not prod.empty:
                prod = prod.iloc[0]
                recommendations.append(RecommendationItem(
                    product_id=rec['product_id'],
                    product_name=str(prod.get('product_name', 'N/A')),
                    category=str(prod.get('category', 'N/A')),
                    price=str(prod.get('discounted_price', 'N/A')),
                    rating=float(prod.get('rating', 0.0)),
                    score=rec['score'],
                    reason=rec['reason']
                ))
        
        return RecommendationResponse(
            query_product_id=request.product_id,
            recommendations=recommendations,
            count=len(recommendations),
            timestamp=datetime.now()
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recommendation failed: {str(e)}")


# ============= PHASE 4: Review Intelligence =============

class ReviewAnalysisRequest(BaseModel):
    product_id: str
    reviews: List[str]


class SentimentAnalysis(BaseModel):
    sentiment: str
    confidence: float
    text: str


class ReviewSummary(BaseModel):
    positive_count: int
    negative_count: int
    neutral_count: int
    overall_sentiment: str
    key_strengths: List[str]
    key_weaknesses: List[str]
    average_confidence: float


class ReviewIntelligenceResponse(BaseModel):
    product_id: str
    analysis: List[SentimentAnalysis]
    summary: ReviewSummary
    timestamp: datetime


@app.post("/analyze-reviews", response_model=ReviewIntelligenceResponse, tags=["Reviews"])
async def analyze_reviews(request: ReviewAnalysisRequest):
    """
    Analyze product reviews using sentiment analysis.
    
    Phase 4: Keyword-based sentiment + review summarization
    
    Args:
        product_id: Product ID
        reviews: List of review texts to analyze
    
    Returns:
        ReviewIntelligenceResponse with sentiment breakdown and key insights
    """
    try:
        # Analyze reviews using simple integration
        analysis_results = analyze_product_reviews(request.reviews)
        
        # Parse results
        sentiments = []
        for review, (sentiment, confidence) in zip(request.reviews, analysis_results['sentiments']):
            sentiments.append(SentimentAnalysis(
                sentiment=sentiment,
                confidence=confidence,
                text=review[:200]  # Truncate for display
            ))
        
        # Create summary
        summary = ReviewSummary(
            positive_count=analysis_results['positive_count'],
            negative_count=analysis_results['negative_count'],
            neutral_count=analysis_results['neutral_count'],
            overall_sentiment=analysis_results['overall_sentiment'],
            key_strengths=analysis_results['key_strengths'][:5],
            key_weaknesses=analysis_results['key_weaknesses'][:5],
            average_confidence=analysis_results['average_confidence']
        )
        
        return ReviewIntelligenceResponse(
            product_id=request.product_id,
            analysis=sentiments,
            summary=summary,
            timestamp=datetime.now()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Review analysis failed: {str(e)}")


# ============= PHASE 5: RAG Copilot =============

class CopilotQuery(BaseModel):
    query: str
    top_k: int = 5
    context: Optional[Dict[str, Any]] = None


class CopilotResponse(BaseModel):
    query: str
    advice: str
    retrieved_products: List[Dict[str, Any]]
    confidence: float
    timestamp: datetime


@app.post("/copilot-advice", response_model=CopilotResponse, tags=["AI Assistant"])
async def get_copilot_advice(request: CopilotQuery):
    """
    Get AI shopping advice using semantic search + RAG.
    
    Phase 5: Vector retrieval + contextual shopping advice
    
    Args:
        query: Shopping question or product discovery request
        top_k: Number of products to retrieve for context
        context: Optional user context (budget, preferences, etc.)
    
    Returns:
        CopilotResponse with AI-generated advice and relevant products
    """
    if embedding_model is None or faiss_index is None:
        raise HTTPException(status_code=503, detail="Search engine not initialized")
    
    try:
        # Encode query
        query_embedding = embedding_model.encode(
            request.query,
            convert_to_numpy=True
        ).astype('float32')
        query_embedding = normalize([query_embedding])[0]
        
        # Retrieve top-k products from FAISS
        distances, indices = faiss_index.search(
            np.array([query_embedding]),
            k=request.top_k
        )
        
        # Build product context
        retrieved_products = []
        for idx in indices[0]:
            product_id = product_ids[idx]
            product = products_df[products_df['product_id'] == product_id]
            if not product.empty:
                prod = product.iloc[0]
                retrieved_products.append({
                    'product_id': product_id,
                    'product_name': str(prod.get('product_name', 'N/A')),
                    'category': str(prod.get('category', 'N/A')),
                    'price': str(prod.get('discounted_price', 'N/A')),
                    'rating': float(prod.get('rating', 0.0))
                })
        
        # Generate advice using simple RAG integration
        advice = generate_shopping_advice(
            query=request.query,
            products=retrieved_products
        )
        
        return CopilotResponse(
            query=request.query,
            advice=advice,
            retrieved_products=retrieved_products,
            confidence=0.85,
            timestamp=datetime.now()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Copilot failed: {str(e)}")


# Run: uvicorn backend.retrieval_api:app --reload --host 0.0.0.0 --port 8000
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
