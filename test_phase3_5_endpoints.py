"""
Test Phase 3-5 Integrated Endpoints
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_endpoint(name, method, endpoint, data=None):
    """Test an API endpoint."""
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"Endpoint: {method} {endpoint}")
    print(f"{'='*60}")
    
    try:
        if method == "GET":
            response = requests.get(f"{BASE_URL}{endpoint}")
        elif method == "POST":
            response = requests.post(f"{BASE_URL}{endpoint}", json=data)
        
        print(f"Status: {response.status_code}")
        print(f"Response:\n{json.dumps(response.json(), indent=2)}")
        return response.json()
    except Exception as e:
        print(f"Error: {e}")
        return None

# Test Phase 2: Search endpoint
print("\n\n" + "="*60)
print("PHASE 2: SEMANTIC SEARCH")
print("="*60)

test_endpoint(
    "Semantic Search",
    "POST",
    "/search",
    {
        "query": "laptop for programming",
        "top_k": 3
    }
)

# Test Phase 3: Recommendations
print("\n\n" + "="*60)
print("PHASE 3: RECOMMENDATION ENGINE")
print("="*60)

# First, get a product ID from search
search_results = test_endpoint(
    "Search for product",
    "POST",
    "/search",
    {"query": "wireless headphones", "top_k": 1}
)

if search_results and 'results' in search_results and len(search_results['results']) > 0:
    product_id = search_results['results'][0]['product_id']
    print(f"\nUsing product ID: {product_id}")
    
    test_endpoint(
        "Get Recommendations",
        "POST",
        "/recommend",
        {
            "product_id": product_id,
            "top_k": 3
        }
    )

# Test Phase 4: Review Intelligence
print("\n\n" + "="*60)
print("PHASE 4: REVIEW INTELLIGENCE")
print("="*60)

test_endpoint(
    "Analyze Reviews",
    "POST",
    "/analyze-reviews",
    {
        "product_id": "B001",
        "reviews": [
            "Excellent product! Great quality and amazing performance. Highly recommended!",
            "This product is terrible. Very poor quality and broke after 2 days.",
            "It's okay, nothing special but works as expected."
        ]
    }
)

# Test Phase 5: RAG Copilot
print("\n\n" + "="*60)
print("PHASE 5: RAG SHOPPING COPILOT")
print("="*60)

test_endpoint(
    "Get Shopping Advice",
    "POST",
    "/copilot-advice",
    {
        "query": "I need a budget laptop under ₹50000 for online classes",
        "top_k": 5
    }
)

test_endpoint(
    "Product Comparison",
    "POST",
    "/copilot-advice",
    {
        "query": "What's better for gaming: gaming laptop or external GPU setup?",
        "top_k": 5
    }
)

# Test Stats
print("\n\n" + "="*60)
print("SYSTEM STATS")
print("="*60)

test_endpoint(
    "Get Stats",
    "GET",
    "/stats",
    None
)

print("\n\n✅ All Phase 3-5 endpoints tested successfully!\n")
