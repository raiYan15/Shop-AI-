# ShopMind AI - MVP Complete ✅

**Status**: Data pipeline + semantic search + FastAPI backend operational

---

## 🎯 What's Done

### Phase 1: Data Pipeline & Embeddings ✅
- **Dataset**: Amazon sales data (1,351 unique products after deduplication)
- **Embedding Model**: SentenceTransformers `all-mpnet-base-v2` (768-dim vectors)
- **Vector Index**: FAISS index with 1,351 embeddings
- **Performance**: ~12s to compute all embeddings

### Phase 2: Semantic Search API ✅
**FastAPI running on `http://localhost:8000`**

#### Available Endpoints:

1. **POST `/search`** - Semantic search with similarity scoring
   ```json
   {
     "query": "laptop for coding",
     "top_k": 5
   }
   ```
   **Response**: Top-k products with similarity scores

2. **GET `/health`** - Health check
   ```
   {
     "status": "healthy",
     "models_loaded": true
   }
   ```

3. **GET `/stats`** - Index statistics
   ```json
   {
     "total_products": 1351,
     "index_vectors": 1351,
     "embedding_dimension": 768,
     "categories": 211,
     "avg_rating": 4.09
   }
   ```

4. **GET `/product/{product_id}`** - Retrieve product details by ID

5. **GET `/search-quick`** - Quick search with query parameters
   ```
   /search-quick?q=laptop&k=5
   ```

---

## 📊 Example Searches

**Query**: "laptop for coding"  
**Results**:
1. Lenovo IdeaPad 3 11th Gen (Similarity: 0.4417, Rating: 4.0)
2. Tarkan Portable Folding Laptop Desk (Similarity: 0.4132, Rating: 4.3)
3. Gizga Essentials Multi-Purpose Desk (Similarity: 0.4116, Rating: 3.6)

---

## 📁 Project Structure

```
.
├── data/
│   ├── amazon.csv                 (1,351 unique products)
│   ├── faiss_index.idx            (FAISS vector index)
│   └── id_map.pkl                 (product ID mapping)
├── backend/
│   └── retrieval_api.py           (FastAPI retrieval server)
├── notebooks/
│   └── semantic_search_demo.ipynb (Jupyter demo notebook)
├── requirements.txt               (Dependencies)
├── setup_venv.bat                 (Python venv setup)
├── setup_conda.bat                (Conda setup)
└── README.md
```

---

## 🚀 Quick Start

### Run API Server
```bash
cd 'C:\Users\dashi\OneDrive\Desktop\Projects\ML project'
python -m uvicorn backend.retrieval_api:app --host 127.0.0.1 --port 8000
```

### Test Endpoints
```bash
python test_api.py
```

### Use Jupyter Notebook
```bash
jupyter notebook notebooks/semantic_search_demo.ipynb
```

---

## 🔧 Dependencies Installed

- `sentence-transformers` - Embedding model
- `faiss-cpu` - Vector similarity search
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `pandas`, `numpy` - Data processing
- `scikit-learn` - ML utilities

---

## ✨ Next Phases (Ready to Implement)

### Phase 3: Recommendation Engine
- Content-based filtering (product features, categories)
- Collaborative filtering (user-product interactions)
- Hybrid recommendations

### Phase 4: Review Intelligence
- BERT-based sentiment analysis
- Review summarization (pros/cons extraction)
- Key insights from thousands of reviews

### Phase 5: RAG Pipeline + LLM
- Vector retrieval + LLM integration
- AI shopping assistant for product comparison
- Explainable recommendations (SHAP)

### Phase 6: Frontend + Full Stack
- React + TypeScript UI
- MongoDB integration
- Real-time notifications
- User authentication (JWT + Google OAuth)

### Phase 7: Deployment
- AWS EC2 / ECS deployment
- MLflow experiment tracking
- Docker containerization
- CI/CD pipeline

---

## 📈 Performance Metrics

| Metric | Value |
|--------|-------|
| Total Products | 1,351 |
| Embedding Dimension | 768 |
| FAISS Index Size | ~3.5MB |
| Embedding Time | ~12s (1,351 products) |
| Search Latency | ~50-100ms |
| Model Size | ~438MB (one-time download) |

---

## 🎓 Portfolio Value

This MVP demonstrates:
✅ **ML/NLP**: SentenceTransformers for semantic embeddings  
✅ **Vector Search**: FAISS index implementation  
✅ **Backend**: FastAPI with async/await patterns  
✅ **Data Pipeline**: CSV ingestion, cleaning, deduplication  
✅ **API Design**: RESTful endpoints with Pydantic validation  
✅ **Scalability**: Modular architecture ready for expansion  

---

## 📝 Notes

- All searches use **cosine similarity** (inner product after normalization)
- Products are deduplicated by `product_id`
- Ratings are stored as concatenated strings in source CSV (handled gracefully)
- FAISS uses `IndexFlatIP` (inner product) for efficient similarity search
- API is stateless and can be horizontally scaled

---

**Ready for Phase 3?** Proceed with recommendation engine or pivot to a different phase.
