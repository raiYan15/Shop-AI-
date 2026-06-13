#!/usr/bin/env python
"""Test backend API endpoints"""
import requests
import json

print('=== Testing Backend API Endpoints ===\n')

BASE_URL = 'http://localhost:8000'

# Test 1: Health
try:
    r = requests.get(f'{BASE_URL}/health', timeout=5)
    data = r.json()
    print('✅ GET /health')
    print(f'   Status: {data.get("status")}')
    print(f'   MongoDB: {data.get("mongodb")}')
    print(f'   FAISS Vectors: {data.get("faiss_vectors")}')
except Exception as e:
    print(f'❌ GET /health: {str(e)[:100]}')

print()

# Test 2: Products
try:
    r = requests.get(f'{BASE_URL}/products', timeout=5)
    data = r.json()
    print('✅ GET /products')
    print(f'   Total: {data.get("total", 0)}')
    print(f'   Limit: {data.get("limit", "N/A")}')
    if data.get('products'):
        print(f'   First product: {data["products"][0].get("title", "N/A")[:50]}')
except Exception as e:
    print(f'❌ GET /products: {str(e)[:100]}')

print()

# Test 3: Search
try:
    r = requests.get(f'{BASE_URL}/search?q=laptop', timeout=5)
    data = r.json()
    print('✅ GET /search?q=laptop')
    print(f'   Results: {len(data.get("results", []))}')
except Exception as e:
    print(f'❌ GET /search: {str(e)[:100]}')

print()

# Test 4: Trending
try:
    r = requests.get(f'{BASE_URL}/trending', timeout=5)
    data = r.json()
    print('✅ GET /trending')
    print(f'   Items: {len(data.get("items", []))}')
except Exception as e:
    print(f'❌ GET /trending: {str(e)[:100]}')

print()

# Test 5: Chat (RAG)
try:
    r = requests.post(f'{BASE_URL}/chat', 
                     json={'message': 'What products are available?', 'top_k': 3},
                     timeout=10)
    data = r.json()
    print('✅ POST /chat')
    print(f'   Response: {str(data.get("response", ""))[:80]}...')
except Exception as e:
    print(f'❌ POST /chat: {str(e)[:100]}')

print('\n=== All Tests Complete ===')
