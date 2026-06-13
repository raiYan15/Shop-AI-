"""
Phase 6: Extended Backend API for MongoDB Integration
Adds endpoints for user management, recommendations, cart, and purchases
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthCredential
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
from typing import List, Optional
import json

# MongoDB models
class User(BaseModel):
    user_id: str
    email: EmailStr
    name: str
    created_at: datetime = None
    updated_at: datetime = None

class WishlistItem(BaseModel):
    product_id: str
    added_at: datetime = None

class CartItem(BaseModel):
    product_id: str
    quantity: int = 1
    added_at: datetime = None

class Purchase(BaseModel):
    product_id: str
    quantity: int
    price: float
    purchased_at: datetime = None

class UserProfile(BaseModel):
    user_id: str
    email: str
    name: str
    preferences: Optional[dict] = None
    purchase_history: List[Purchase] = []
    wishlist: List[WishlistItem] = []
    cart: List[CartItem] = []

class RecommendationResponse(BaseModel):
    user_id: str
    recommendations: List[dict]
    timestamp: datetime

# Extended API routes for Phase 6
api_routes = """
# Phase 6 API Endpoints (Ready for MongoDB)

## User Management
POST /api/users/register
- Register new user
- Body: {email, name, password}
- Returns: {user_id, token}

POST /api/users/login
- User login
- Body: {email, password}
- Returns: {user_id, token, expires_in}

GET /api/users/profile
- Get user profile
- Headers: Authorization: Bearer {token}
- Returns: {user_id, email, name, preferences}

## Wishlist Management
POST /api/wishlist/add/{product_id}
- Add product to wishlist
- Returns: {wishlist}

GET /api/wishlist
- Get user's wishlist
- Returns: List[products]

DELETE /api/wishlist/{product_id}
- Remove from wishlist

## Cart Management
POST /api/cart/add
- Add to cart
- Body: {product_id, quantity}
- Returns: {cart}

GET /api/cart
- Get current cart
- Returns: List[cart_items]

PUT /api/cart/{product_id}
- Update cart item quantity
- Body: {quantity}

DELETE /api/cart/{product_id}
- Remove from cart

## Recommendations
GET /api/recommendations
- Get personalized recommendations for user
- Returns: {recommendations}

POST /api/recommendations/feedback
- Send recommendation feedback
- Body: {product_id, relevant: true/false}

## Purchase History
GET /api/purchases
- Get user's purchase history
- Returns: List[purchases]

POST /api/purchases/checkout
- Create purchase order
- Body: {items, shipping_address}
- Returns: {order_id, total_price}

## Behavior Tracking
POST /api/events/view
- Track product view
- Body: {product_id}

POST /api/events/search
- Track search query
- Body: {query}

POST /api/events/click
- Track product click
- Body: {product_id}

## Analytics
GET /api/analytics/user-behavior
- Get user behavior insights
- Returns: {views, searches, clicks}

GET /api/analytics/product-stats
- Get product statistics
- Returns: {popularity, avg_rating, purchase_count}
"""

# MongoDB Collections Structure
mongo_collections = """
# Phase 6: MongoDB Collections Schema

## Users Collection
{
  "_id": ObjectId(),
  "user_id": "USER_123",
  "email": "user@example.com",
  "name": "John Doe",
  "password_hash": "...",
  "created_at": ISODate(),
  "updated_at": ISODate(),
  "preferences": {
    "categories": ["Computers", "Electronics"],
    "price_range": [10000, 100000],
    "preferred_brands": ["Lenovo", "Dell"]
  }
}

## Products Collection (denormalized from CSV)
{
  "_id": ObjectId(),
  "product_id": "B07JW9H4J1",
  "product_name": "...",
  "category": "...",
  "price": 399,
  "rating": 4.2,
  "description": "...",
  "embedding": [...],  // 768-dim vector
  "created_at": ISODate(),
  "updated_at": ISODate()
}

## Recommendations Collection
{
  "_id": ObjectId(),
  "user_id": "USER_123",
  "product_id": "B07JW9H4J1",
  "score": 0.85,
  "reason": "content_based",  // content_based, collab, hybrid
  "created_at": ISODate(),
  "expires_at": ISODate()  // TTL index for auto-cleanup
}

## Wishlist Collection
{
  "_id": ObjectId(),
  "user_id": "USER_123",
  "product_id": "B07JW9H4J1",
  "added_at": ISODate()
}

## Cart Collection
{
  "_id": ObjectId(),
  "user_id": "USER_123",
  "items": [
    {
      "product_id": "B07JW9H4J1",
      "quantity": 2,
      "price": 399,
      "added_at": ISODate()
    }
  ],
  "total": 798,
  "updated_at": ISODate()
}

## Purchases Collection
{
  "_id": ObjectId(),
  "order_id": "ORD_123",
  "user_id": "USER_123",
  "items": [...],
  "total_price": 798,
  "shipping_address": {...},
  "status": "delivered",  // pending, shipped, delivered
  "created_at": ISODate(),
  "updated_at": ISODate()
}

## User Behavior Collection
{
  "_id": ObjectId(),
  "user_id": "USER_123",
  "event_type": "view",  // view, search, click, purchase
  "product_id": "B07JW9H4J1",
  "query": "laptop for coding",
  "timestamp": ISODate()
}

## Reviews Collection
{
  "_id": ObjectId(),
  "user_id": "USER_123",
  "product_id": "B07JW9H4J1",
  "rating": 4.5,
  "title": "Great product!",
  "content": "...",
  "sentiment": "POSITIVE",
  "helpful_count": 10,
  "created_at": ISODate()
}

## Searches Collection
{
  "_id": ObjectId(),
  "user_id": "USER_123",
  "query": "laptop for coding",
  "results_count": 45,
  "clicked_product": "B07JW9H4J1",
  "timestamp": ISODate()
}
"""

# MongoDB Indexes for Performance
mongo_indexes = """
# Phase 6: MongoDB Indexes (TTL, Compound, Text Search)

## Users
db.users.createIndex({ "email": 1 }, { unique: true })
db.users.createIndex({ "user_id": 1 }, { unique: true })

## Products
db.products.createIndex({ "product_id": 1 }, { unique: true })
db.products.createIndex({ "category": 1 })
db.products.createIndex({ "rating": -1 })
db.products.createIndex({ "product_name": "text", "description": "text" })

## Recommendations
db.recommendations.createIndex({ "user_id": 1, "created_at": -1 })
db.recommendations.createIndex({ "expires_at": 1 }, { expireAfterSeconds: 0 })

## Wishlist
db.wishlist.createIndex({ "user_id": 1 })
db.wishlist.createIndex({ "product_id": 1 })
db.wishlist.createIndex({ "user_id": 1, "product_id": 1 }, { unique: true })

## Cart
db.cart.createIndex({ "user_id": 1 }, { unique: true })

## Purchases
db.purchases.createIndex({ "user_id": 1, "created_at": -1 })
db.purchases.createIndex({ "order_id": 1 }, { unique: true })

## User Behavior
db.user_behavior.createIndex({ "user_id": 1, "timestamp": -1 })
db.user_behavior.createIndex({ "event_type": 1 })
db.user_behavior.createIndex({ "timestamp": -1 })

## Reviews
db.reviews.createIndex({ "product_id": 1, "rating": -1 })
db.reviews.createIndex({ "user_id": 1 })
db.reviews.createIndex({ "sentiment": 1 })

## Searches
db.searches.createIndex({ "user_id": 1, "timestamp": -1 })
db.searches.createIndex({ "query": "text" })
"""

def generate_phase6_docs():
    """Generate Phase 6 documentation."""
    print("\n" + "="*80)
    print("PHASE 6: REACT FRONTEND + MONGODB - BACKEND DESIGN")
    print("="*80)
    
    print("\n" + "-"*80)
    print("EXTENDED API ENDPOINTS")
    print("-"*80)
    print(api_routes)
    
    print("\n" + "-"*80)
    print("MONGODB COLLECTIONS SCHEMA")
    print("-"*80)
    print(mongo_collections)
    
    print("\n" + "-"*80)
    print("MONGODB INDEXES FOR OPTIMIZATION")
    print("-"*80)
    print(mongo_indexes)
    
    print("\n✓ Phase 6 backend design complete!")

if __name__ == "__main__":
    generate_phase6_docs()
