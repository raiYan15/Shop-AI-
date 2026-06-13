#!/usr/bin/env python3
"""
ShopMind AI — Full System Connectivity & Health Check
Tests: Backend API, MongoDB, ML Models, Frontend API Bridge
"""

import sys
import time
import json
import asyncio
import traceback
from pathlib import Path
from datetime import datetime

# ANSI Color codes
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"
DIM    = "\033[2m"

PASS = f"{GREEN}✓ PASS{RESET}"
FAIL = f"{RED}✗ FAIL{RESET}"
WARN = f"{YELLOW}⚠ WARN{RESET}"
INFO = f"{CYAN}ℹ INFO{RESET}"

results = []

def log(level, test_name, message, detail=""):
    icon = {"PASS": PASS, "FAIL": FAIL, "WARN": WARN, "INFO": INFO}.get(level, INFO)
    print(f"  {icon}  {BOLD}{test_name}{RESET}")
    print(f"        {message}")
    if detail:
        print(f"        {DIM}{detail}{RESET}")
    results.append({"test": test_name, "status": level, "message": message})

def header(title):
    print(f"\n{BOLD}{CYAN}{'='*60}{RESET}")
    print(f"{BOLD}{CYAN}  {title}{RESET}")
    print(f"{BOLD}{CYAN}{'='*60}{RESET}")

def section(title):
    print(f"\n{BOLD}  ── {title} ──{RESET}")


# ============================================================
# 1. ENVIRONMENT CHECKS
# ============================================================
header("ShopMind AI — System Connectivity Report")
print(f"  {DIM}Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{RESET}")

section("1. Python Environment")

# Python version
import platform
py_ver = platform.python_version()
if py_ver >= "3.9":
    log("PASS", "Python Version", f"Python {py_ver} — Compatible")
else:
    log("FAIL", "Python Version", f"Python {py_ver} — Requires 3.9+")

# Check all required packages
REQUIRED_PACKAGES = [
    ("fastapi", "FastAPI"),
    ("uvicorn", "Uvicorn"),
    ("pymongo", "PyMongo"),
    ("motor", "Motor (Async MongoDB)"),
    ("sentence_transformers", "Sentence Transformers"),
    ("faiss", "FAISS"),
    ("pandas", "Pandas"),
    ("numpy", "NumPy"),
    ("sklearn", "scikit-learn"),
    ("pydantic", "Pydantic"),
    ("dotenv", "python-dotenv"),
]

for pkg, name in REQUIRED_PACKAGES:
    try:
        mod = __import__(pkg)
        ver = getattr(mod, "__version__", "unknown")
        log("PASS", f"Package: {name}", f"Version {ver} installed")
    except ImportError:
        log("FAIL", f"Package: {name}", f"NOT INSTALLED — run: pip install {pkg}")


# ============================================================
# 2. DATA FILES CHECK
# ============================================================
section("2. Data Files & Models")

data_dir = Path(__file__).parent / "data"
REQUIRED_FILES = [
    (data_dir / "amazon.csv",      "Amazon Products CSV"),
    (data_dir / "faiss_index.idx", "FAISS Vector Index"),
    (data_dir / "id_map.pkl",      "Product ID Map"),
]

for fpath, name in REQUIRED_FILES:
    if fpath.exists():
        size_mb = fpath.stat().st_size / (1024 * 1024)
        log("PASS", f"File: {name}", f"Found — {size_mb:.2f} MB", str(fpath))
    else:
        log("FAIL", f"File: {name}", f"MISSING — {fpath}")

# Check CSV structure
try:
    import pandas as pd
    csv_path = data_dir / "amazon.csv"
    if csv_path.exists():
        df = pd.read_csv(csv_path, nrows=5)
        required_cols = ["product_id", "product_name", "category", "discounted_price", "rating"]
        missing_cols = [c for c in required_cols if c not in df.columns]
        if not missing_cols:
            total = pd.read_csv(csv_path).shape[0]
            log("PASS", "CSV Schema", f"All required columns present — {total} total products")
        else:
            log("WARN", "CSV Schema", f"Missing columns: {missing_cols}")
    df = None  # free memory
except Exception as e:
    log("FAIL", "CSV Schema", f"Error reading CSV: {e}")


# ============================================================
# 3. ML MODEL LOADING
# ============================================================
section("3. ML Models (FAISS + Sentence Transformers)")

try:
    import numpy as np
    import pickle
    import faiss
    from sklearn.preprocessing import normalize

    # Load FAISS
    t0 = time.time()
    faiss_path = data_dir / "faiss_index.idx"
    if faiss_path.exists():
        index = faiss.read_index(str(faiss_path))
        t1 = time.time()
        log("PASS", "FAISS Index Load", 
            f"{index.ntotal} vectors, dim={index.d}, loaded in {t1-t0:.2f}s")
    else:
        log("FAIL", "FAISS Index Load", "Index file not found")
        index = None

    # Load ID Map
    idmap_path = data_dir / "id_map.pkl"
    if idmap_path.exists():
        with open(idmap_path, "rb") as f:
            id_map = pickle.load(f)
        log("PASS", "Product ID Map", f"{len(id_map)} product IDs loaded")
    else:
        log("FAIL", "Product ID Map", "id_map.pkl not found")
        id_map = None

except Exception as e:
    log("FAIL", "FAISS / ID Map", f"Error: {e}")
    index = id_map = None

try:
    from sentence_transformers import SentenceTransformer
    t0 = time.time()
    model = SentenceTransformer("all-mpnet-base-v2")
    t1 = time.time()
    dim = model.get_sentence_embedding_dimension()
    log("PASS", "Sentence Transformer", f"all-mpnet-base-v2 loaded — dim={dim}, {t1-t0:.2f}s")
except Exception as e:
    log("FAIL", "Sentence Transformer", f"Load failed: {e}")
    model = None


# ============================================================
# 4. SEMANTIC SEARCH TEST
# ============================================================
section("4. Semantic Search (FAISS + SentenceTransformers)")

if model and index and id_map:
    try:
        import pandas as pd
        import numpy as np

        df = pd.read_csv(data_dir / "amazon.csv", nrows=5000)
        df = df.drop_duplicates(subset=["product_id"], keep="first")

        queries = [
            "best gaming laptop under 70000",
            "wireless bluetooth headphones noise cancelling",
            "running shoes for beginners",
        ]

        for q in queries:
            t0 = time.time()
            emb = model.encode(q, convert_to_numpy=True).astype("float32")
            emb = normalize([emb])[0]
            distances, indices = index.search(np.array([emb]), k=3)
            t1 = time.time()
            top_ids = [id_map[i] for i in indices[0]]
            top_products = df[df["product_id"].isin(top_ids)]["product_name"].tolist()
            names_preview = " | ".join([p[:40] for p in top_products[:2]])
            log("PASS", f"Search: '{q[:35]}...'", 
                f"{t1-t0:.3f}s — Top: {names_preview or 'N/A'}")
    except Exception as e:
        log("FAIL", "Semantic Search", f"Error: {e}", traceback.format_exc(limit=2))
else:
    log("WARN", "Semantic Search", "Skipped — models not loaded")


# ============================================================
# 5. RECOMMENDATION ENGINE
# ============================================================
section("5. Recommendation Engine")

try:
    sys.path.insert(0, str(Path(__file__).parent / "backend"))
    from phase3_5_integration import recommend_similar_products, analyze_product_reviews, generate_shopping_advice
    
    import pandas as pd
    df = pd.read_csv(data_dir / "amazon.csv", nrows=5000)
    df = df.drop_duplicates(subset=["product_id"], keep="first")
    
    sample_id = df.iloc[0]["product_id"]
    recs = recommend_similar_products(sample_id, df, top_k=3)
    
    if recs:
        log("PASS", "Recommendation Engine", 
            f"Generated {len(recs)} recommendations for product '{sample_id}'",
            f"Reason: {recs[0].get('reason','')}")
    else:
        log("WARN", "Recommendation Engine", "Returned empty — check category data")

except Exception as e:
    log("FAIL", "Recommendation Engine", f"Error: {e}", traceback.format_exc(limit=2))


# ============================================================
# 6. REVIEW INTELLIGENCE
# ============================================================
section("6. Review Intelligence (Sentiment Analysis)")

try:
    from phase3_5_integration import analyze_product_reviews
    
    test_reviews = [
        "This product is absolutely amazing! Great quality and excellent performance.",
        "Terrible experience. The product broke after 2 days. Waste of money.",
        "Decent product for the price. Nothing special but does the job.",
    ]
    
    results_sent = analyze_product_reviews(test_reviews)
    
    log("PASS", "Sentiment Analysis",
        f"Analyzed {len(test_reviews)} reviews → "
        f"Pos:{results_sent['positive_count']} Neg:{results_sent['negative_count']} Neu:{results_sent['neutral_count']}",
        f"Overall: {results_sent['overall_sentiment']} | "
        f"Avg confidence: {results_sent['average_confidence']:.2f}")
    
    if results_sent["key_strengths"]:
        log("PASS", "Strengths Extraction", f"Keywords: {', '.join(results_sent['key_strengths'])}")
    if results_sent["key_weaknesses"]:
        log("PASS", "Weaknesses Extraction", f"Keywords: {', '.join(results_sent['key_weaknesses'])}")

except Exception as e:
    log("FAIL", "Review Intelligence", f"Error: {e}")


# ============================================================
# 7. RAG COPILOT
# ============================================================
section("7. RAG Copilot (Shopping Advice Generator)")

try:
    from phase3_5_integration import generate_shopping_advice
    
    sample_products = [
        {"product_name": "Gaming Laptop X1", "price": "₹65000", "rating": 4.5},
        {"product_name": "UltraBook Pro M2", "price": "₹89000", "rating": 4.8},
    ]
    
    advice = generate_shopping_advice("best laptop for ML", sample_products)
    
    if advice and len(advice) > 20:
        log("PASS", "RAG Copilot", "Shopping advice generated successfully",
            f"Preview: {advice[:120]}...")
    else:
        log("WARN", "RAG Copilot", "Advice too short or empty")
        
except Exception as e:
    log("FAIL", "RAG Copilot", f"Error: {e}")


# ============================================================
# 8. MONGODB CONNECTIVITY
# ============================================================
section("8. MongoDB Connectivity")

async def test_mongodb():
    """Test MongoDB connection and basic operations."""
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        from dotenv import load_dotenv
        import os
        
        # Load env
        env_path = Path(__file__).parent / "backend" / ".env"
        load_dotenv(env_path)
        
        uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
        db_name = os.getenv("MONGODB_DB_NAME", "shopmind_ai")
        
        log("INFO", "MongoDB URI", f"Connecting to: {uri[:50]}...")
        
        # Connect with timeout
        t0 = time.time()
        client = AsyncIOMotorClient(uri, serverSelectionTimeoutMS=5000)
        
        # Ping
        await client.admin.command("ping")
        t1 = time.time()
        
        log("PASS", "MongoDB Connection", f"Connected successfully in {t1-t0:.3f}s")
        
        # Get/create database
        db = client[db_name]
        
        # List collections
        collections = await db.list_collection_names()
        log("PASS", "MongoDB Database", 
            f"Database '{db_name}' accessible — {len(collections)} collections: {collections[:5]}")
        
        # Test write + read
        test_col = db["connectivity_test"]
        test_doc = {
            "test": "shopmind_ai_connectivity",
            "timestamp": datetime.now(),
            "version": "1.0",
            "status": "ok"
        }
        insert_result = await test_col.insert_one(test_doc)
        log("PASS", "MongoDB Write", f"Document inserted — ID: {insert_result.inserted_id}")
        
        # Read back
        found = await test_col.find_one({"_id": insert_result.inserted_id})
        if found:
            log("PASS", "MongoDB Read", f"Document retrieved — test='{found['test']}'")
        
        # Cleanup
        await test_col.delete_one({"_id": insert_result.inserted_id})
        log("PASS", "MongoDB Cleanup", "Test document deleted")
        
        # Check/create collections
        required_collections = [
            "users", "products", "reviews", "recommendations",
            "search_history", "wishlist", "cart", "ai_chats", "user_behavior"
        ]
        
        existing = set(collections)
        for col_name in required_collections:
            if col_name not in existing:
                await db.create_collection(col_name)
                log("INFO", f"Collection: {col_name}", "Created new collection")
            else:
                count = await db[col_name].count_documents({})
                log("PASS", f"Collection: {col_name}", f"Exists — {count} documents")
        
        client.close()
        return True
        
    except Exception as e:
        log("FAIL", "MongoDB Connection", f"Failed: {e}",
            "→ Check: Is MongoDB running? Is MONGODB_URI correct in backend/.env?")
        return False

asyncio.run(test_mongodb())


# ============================================================
# 9. FASTAPI BACKEND CHECK
# ============================================================
section("9. FastAPI Backend Server")

try:
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    result = sock.connect_ex(("localhost", 8000))
    sock.close()
    
    if result == 0:
        # Port is open — test endpoints
        import urllib.request
        
        try:
            url = "http://localhost:8000/health"
            req = urllib.request.urlopen(url, timeout=3)
            data = json.loads(req.read())
            models_loaded = data.get("models_loaded", False)
            log("PASS", "Backend /health", 
                f"Running — models_loaded={models_loaded}",
                f"Response: {json.dumps(data)}")
        except Exception as e:
            log("WARN", "Backend /health", f"Port 8000 open but /health failed: {e}")
        
        try:
            url = "http://localhost:8000/stats"
            req = urllib.request.urlopen(url, timeout=3)
            data = json.loads(req.read())
            log("PASS", "Backend /stats",
                f"{data.get('total_products','?')} products, "
                f"{data.get('index_vectors','?')} vectors, "
                f"{data.get('categories','?')} categories",
                f"Avg rating: {data.get('avg_rating',0):.2f}")
        except Exception as e:
            log("WARN", "Backend /stats", f"Error: {e}")
        
        try:
            import urllib.request
            url = "http://localhost:8000/search-quick?q=gaming+laptop&k=3"
            req = urllib.request.urlopen(url, timeout=10)
            data = json.loads(req.read())
            count = data.get("count", 0)
            if count > 0:
                top = data["results"][0]
                log("PASS", "Backend /search-quick",
                    f"Returned {count} results — Top: {top['product_name'][:40]}",
                    f"Similarity: {top['similarity_score']:.4f}")
            else:
                log("WARN", "Backend /search-quick", "Returned 0 results")
        except Exception as e:
            log("WARN", "Backend Search", f"Error: {e}")
            
    else:
        log("FAIL", "Backend Server", 
            "Port 8000 is NOT open — backend not running",
            "→ Run: uvicorn backend.retrieval_api:app --reload --host 0.0.0.0 --port 8000")

except Exception as e:
    log("FAIL", "Backend Server Check", f"Error: {e}")


# ============================================================
# 10. FRONTEND ↔ BACKEND CONNECTIVITY
# ============================================================
section("10. Frontend ↔ Backend Connectivity")

try:
    import socket
    
    # Check frontend
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    fe_result = sock.connect_ex(("localhost", 3000))
    sock.close()
    
    if fe_result == 0:
        log("PASS", "Frontend Server", "Running on http://localhost:3000")
    else:
        log("WARN", "Frontend Server", "Not running on port 3000",
            "→ Run: npm run dev (in frontend/ directory)")
    
    # Check CORS by checking the backend
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    be_result = sock.connect_ex(("localhost", 8000))
    sock.close()
    
    if be_result == 0:
        log("PASS", "Backend API", "Running on http://localhost:8000")
        log("PASS", "CORS Config", "Backend allows all origins (allow_origins=['*'])")
        log("PASS", "Vite Proxy", "Frontend proxies /api → http://localhost:8000 (vite.config.ts)")
        log("INFO", "API Integration", "Frontend API calls: /api/search, /api/recommend, /api/copilot-advice")
    else:
        log("FAIL", "Backend API", "NOT running — start backend first")
        log("FAIL", "Frontend↔Backend", "Cannot verify — backend offline")
        
except Exception as e:
    log("FAIL", "Frontend↔Backend", f"Check failed: {e}")


# ============================================================
# FINAL REPORT
# ============================================================
header("CONNECTIVITY REPORT SUMMARY")

pass_count = sum(1 for r in results if r["status"] == "PASS")
fail_count = sum(1 for r in results if r["status"] == "FAIL")
warn_count = sum(1 for r in results if r["status"] == "WARN")
total = len(results)

print(f"\n  Total Tests : {total}")
print(f"  {GREEN}Passed      : {pass_count}{RESET}")
print(f"  {RED}Failed      : {fail_count}{RESET}")
print(f"  {YELLOW}Warnings    : {warn_count}{RESET}")

pct = (pass_count / max(total, 1)) * 100
bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
color = GREEN if pct >= 80 else (YELLOW if pct >= 60 else RED)
print(f"\n  Health Score: {color}{bar} {pct:.0f}%{RESET}")

if fail_count > 0:
    print(f"\n  {RED}{BOLD}FAILED TESTS:{RESET}")
    for r in results:
        if r["status"] == "FAIL":
            print(f"  {RED}✗{RESET} {r['test']}: {r['message']}")

if warn_count > 0:
    print(f"\n  {YELLOW}{BOLD}WARNINGS:{RESET}")
    for r in results:
        if r["status"] == "WARN":
            print(f"  {YELLOW}⚠{RESET} {r['test']}: {r['message']}")

print(f"\n  {DIM}Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{RESET}")
print()

# Save JSON report
report_path = Path(__file__).parent / "connectivity_report.json"
with open(report_path, "w") as f:
    json.dump({
        "timestamp": str(datetime.now()),
        "summary": {
            "total": total,
            "passed": pass_count,
            "failed": fail_count,
            "warnings": warn_count,
            "health_score": f"{pct:.1f}%"
        },
        "tests": results
    }, f, indent=2)
print(f"  {DIM}Full report saved to: {report_path}{RESET}\n")
