import requests
import json
import time

time.sleep(3)

# Test 1: Health check
print('=== TEST 1: Health Check ===')
resp = requests.get('http://127.0.0.1:8000/health')
print(json.dumps(resp.json(), indent=2))
print()

# Test 2: Search
print('=== TEST 2: Semantic Search ===')
payload = {'query': 'laptop for coding', 'top_k': 3}
resp = requests.post('http://127.0.0.1:8000/search', json=payload)
result = resp.json()
print(f'Query: {result["query"]}')
print(f'Found: {result["count"]} results')
for i, r in enumerate(result['results'], 1):
    print(f'{i}. {r["product_name"][:50]}...')
    print(f'   Similarity: {r["similarity_score"]:.4f} | Rating: {r["rating"]}')
print()

# Test 3: Stats
print('=== TEST 3: Index Statistics ===')
try:
    resp = requests.get('http://127.0.0.1:8000/stats')
    if resp.status_code == 200:
        print(json.dumps(resp.json(), indent=2))
    else:
        print(f'Status: {resp.status_code}')
        print(resp.text)
except Exception as e:
    print(f'Error: {e}')

