#!/usr/bin/env python3
"""
ShopMind AI - Comprehensive System Test Suite
Tests: Backend API, Database, ML Models, Frontend, Integrations
"""

import sys
import asyncio
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple

# ANSI Colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

PROJECT_ROOT = Path(__file__).parent
BACKEND_ROOT = PROJECT_ROOT / "backend"
TEST_RESULTS = {
    "timestamp": datetime.now().isoformat(),
    "tests": {},
    "summary": {
        "passed": 0,
        "failed": 0,
        "skipped": 0,
        "total": 0,
    }
}

def test_result(name: str, passed: bool, details: str = "") -> None:
    """Record a test result."""
    TEST_RESULTS["tests"][name] = {
        "passed": passed,
        "details": details,
    }
    
    if passed:
        TEST_RESULTS["summary"]["passed"] += 1
        status = f"{GREEN}✓ PASS{RESET}"
    else:
        TEST_RESULTS["summary"]["failed"] += 1
        status = f"{RED}✗ FAIL{RESET}"
    
    TEST_RESULTS["summary"]["total"] += 1
    print(f"  {status} {name}")
    if details:
        print(f"     {details}")

# ===================================================================
#                    SYSTEM COMPONENT TESTS
# ===================================================================

def test_imports():
    """Test all critical imports."""
    print(f"\n{BOLD}{CYAN}Testing Critical Imports{RESET}")
    
    imports_to_test = [
        ("FastAPI", "fastapi"),
        ("Motor (MongoDB async)", "motor.motor_asyncio"),
        ("PyMongo", "pymongo"),
        ("Sentence Transformers", "sentence_transformers"),
        ("FAISS", "faiss"),
        ("Pandas", "pandas"),
        ("NumPy", "numpy"),
        ("APScheduler", "apscheduler"),
        ("Pydantic", "pydantic"),
        ("Uvicorn", "uvicorn"),
    ]
    
    for name, module_name in imports_to_test:
        try:
            __import__(module_name)
            test_result(name, True)
        except ImportError as e:
            test_result(name, False, f"Import failed: {e}")

def test_backend_structure():
    """Test backend file structure."""
    print(f"\n{BOLD}{CYAN}Testing Backend Structure{RESET}")
    
    required_files = [
        ("main_api.py", BACKEND_ROOT / "main_api.py"),
        ("scheduler.py", BACKEND_ROOT / "scheduler.py"),
        ("services/__init__.py", BACKEND_ROOT / "services" / "__init__.py"),
        ("services/db.py", BACKEND_ROOT / "services" / "db.py"),
        ("services/embedding_service.py", BACKEND_ROOT / "services" / "embedding_service.py"),
        ("services/search_service.py", BACKEND_ROOT / "services" / "search_service.py"),
        ("services/recommendation_service.py", BACKEND_ROOT / "services" / "recommendation_service.py"),
        ("services/rag_service.py", BACKEND_ROOT / "services" / "rag_service.py"),
        ("services/pipeline.py", BACKEND_ROOT / "services" / "pipeline.py"),
    ]
    
    for name, filepath in required_files:
        exists = filepath.exists()
        test_result(name, exists, f"Path: {filepath}")

def test_data_files():
    """Test data files exist."""
    print(f"\n{BOLD}{CYAN}Testing Data Files{RESET}")
    
    required_data = [
        ("FAISS Index", PROJECT_ROOT / "data" / "faiss_live.idx"),
        ("Data CSV", PROJECT_ROOT / "data" / "amazon.csv"),
    ]
    
    for name, filepath in required_data:
        exists = filepath.exists()
        size_info = f"({filepath.stat().st_size / (1024*1024):.1f} MB)" if exists else ""
        test_result(name, exists, size_info)

async def test_mongodb_connection():
    """Test MongoDB connectivity."""
    print(f"\n{BOLD}{CYAN}Testing MongoDB Connection{RESET}")
    
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        import os
        from dotenv import load_dotenv
        
        env_file = BACKEND_ROOT / ".env"
        load_dotenv(env_file)
        
        uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
        db_name = os.getenv("MONGODB_DB_NAME", "shopmind_ai")
        
        print(f"  URI: {uri[:50]}...")
        print(f"  Database: {db_name}")
        
        # Try connection
        client = AsyncIOMotorClient(
            uri,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            tlsAllowInvalidCertificates=True,
        )
        
        # Ping
        await client.admin.command("ping")
        client.close()
        
        test_result("MongoDB Connection", True, "Connected successfully")
        
    except Exception as e:
        test_result("MongoDB Connection", False, f"Connection error: {str(e)[:100]}")

async def test_embedding_model():
    """Test embedding model loading."""
    print(f"\n{BOLD}{CYAN}Testing ML Models{RESET}")
    
    try:
        from sentence_transformers import SentenceTransformer
        
        print(f"  Loading embedding model...")
        model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        
        # Test encoding
        test_text = "laptop for coding"
        embedding = model.encode(test_text)
        
        test_result("Embedding Model Load", True, f"Dimension: {len(embedding)}")
        test_result("Text Encoding", True, f"Encoded '{test_text}' → {len(embedding)} dims")
        
    except Exception as e:
        test_result("Embedding Model", False, f"Model error: {e}")

async def test_faiss_index():
    """Test FAISS index."""
    print(f"\n{BOLD}{CYAN}Testing FAISS Index{RESET}")
    
    try:
        import faiss
        import pickle
        
        faiss_path = PROJECT_ROOT / "data" / "faiss_live.idx"
        id_map_path = PROJECT_ROOT / "data" / "id_map_live.pkl"
        
        if faiss_path.exists():
            index = faiss.read_index(str(faiss_path))
            test_result("FAISS Index Load", True, f"Vectors: {index.ntotal}")
            
            if id_map_path.exists():
                with open(id_map_path, 'rb') as f:
                    id_map = pickle.load(f)
                test_result("FAISS ID Map", True, f"IDs: {len(id_map)}")
            else:
                test_result("FAISS ID Map", False, "ID map file missing")
        else:
            test_result("FAISS Index", False, "Index file missing")
            
    except Exception as e:
        test_result("FAISS Operations", False, f"Error: {e}")

def test_backend_config():
    """Test backend configuration."""
    print(f"\n{BOLD}{CYAN}Testing Backend Configuration{RESET}")
    
    try:
        from dotenv import load_dotenv
        import os
        
        env_file = BACKEND_ROOT / ".env"
        load_dotenv(env_file)
        
        required_vars = [
            "MONGODB_URI",
            "MONGODB_DB_NAME",
            "LOG_LEVEL",
            "PIPELINE_INTERVAL_HOURS",
        ]
        
        for var in required_vars:
            value = os.getenv(var)
            if value:
                masked = value[:15] + "***" if len(value) > 15 else value
                test_result(f"ENV: {var}", True, masked)
            else:
                test_result(f"ENV: {var}", False, "Not set")
                
    except Exception as e:
        test_result("Configuration", False, f"Config error: {e}")

def test_frontend_structure():
    """Test frontend file structure."""
    print(f"\n{BOLD}{CYAN}Testing Frontend Structure{RESET}")
    
    frontend_root = PROJECT_ROOT / "frontend"
    
    required_files = [
        ("package.json", frontend_root / "package.json"),
        ("tsconfig.json", frontend_root / "tsconfig.json"),
        ("vite.config.ts", frontend_root / "vite.config.ts"),
        ("src/main.tsx", frontend_root / "src" / "main.tsx"),
        ("src/App.tsx", frontend_root / "src" / "App.tsx"),
        (".env.local", frontend_root / ".env.local"),
    ]
    
    for name, filepath in required_files:
        exists = filepath.exists()
        test_result(name, exists)

# ===================================================================
#                           MAIN RUNNER
# ===================================================================

async def run_all_tests():
    """Run complete test suite."""
    print(f"\n{BOLD}{CYAN}{'='*60}")
    print(f"  SHOPMIND AI - COMPREHENSIVE SYSTEM TEST SUITE")
    print(f"  Started: {datetime.now().isoformat()}")
    print(f"{'='*60}{RESET}\n")
    
    # Synchronous tests
    test_imports()
    test_backend_structure()
    test_data_files()
    test_backend_config()
    test_frontend_structure()
    
    # Async tests
    await test_mongodb_connection()
    await test_embedding_model()
    await test_faiss_index()
    
    # Print summary
    print(f"\n{BOLD}{CYAN}{'='*60}")
    print(f"  TEST SUMMARY")
    print(f"{'='*60}{RESET}\n")
    
    summary = TEST_RESULTS["summary"]
    print(f"  {GREEN}Passed:{RESET}  {summary['passed']}/{summary['total']}")
    print(f"  {RED}Failed:{RESET}  {summary['failed']}/{summary['total']}")
    
    if summary["failed"] == 0:
        print(f"\n{GREEN}{BOLD}✓ ALL TESTS PASSED!{RESET}")
        status = "HEALTHY"
    elif summary["failed"] < summary["total"] * 0.3:
        print(f"\n{YELLOW}{BOLD}⚠ SOME TESTS FAILED{RESET}")
        status = "DEGRADED"
    else:
        print(f"\n{RED}{BOLD}✗ CRITICAL FAILURES{RESET}")
        status = "CRITICAL"
    
    print(f"  Overall Status: {status}\n")
    
    # Save results
    results_file = PROJECT_ROOT / "TEST_RESULTS.json"
    with open(results_file, 'w') as f:
        json.dump(TEST_RESULTS, f, indent=2, default=str)
    
    print(f"{GREEN}✓ Results saved to {results_file}{RESET}")
    
    return TEST_RESULTS

# ===================================================================
#                         ENTRY POINT
# ===================================================================

async def main():
    try:
        await run_all_tests()
        sys.exit(0)
    except Exception as e:
        print(f"\n{RED}TEST SUITE FAILED: {e}{RESET}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
