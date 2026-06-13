"""
Phase 6: MongoDB Schema Design & Initialization
ShopMind AI Database Collections
"""

MONGODB_SCHEMA = {
    "databases": {
        "shopmind_ai": {
            "collections": {
                "users": {
                    "description": "User profiles and authentication",
                    "fields": {
                        "user_id": "ObjectId (primary key)",
                        "email": "string (unique, indexed)",
                        "name": "string",
                        "password_hash": "string (bcrypt)",
                        "profile_picture": "string (URL)",
                        "preferences": {
                            "categories": "array of preferred categories",
                            "budget_min": "number",
                            "budget_max": "number",
                            "language": "string",
                            "theme": "light/dark"
                        },
                        "created_at": "timestamp",
                        "updated_at": "timestamp",
                        "is_active": "boolean"
                    },
                    "indexes": ["email", "created_at"]
                },
                
                "products": {
                    "description": "Product catalog (denormalized from CSV)",
                    "fields": {
                        "product_id": "string (unique, indexed)",
                        "product_name": "string",
                        "category": "string (indexed)",
                        "description": "string",
                        "features": "array of strings",
                        "brand": "string",
                        "original_price": "number",
                        "discounted_price": "number",
                        "discount_percent": "number",
                        "rating": "number (1-5)",
                        "rating_count": "number",
                        "in_stock": "boolean",
                        "images": "array of URLs",
                        "embedding": "array (768-dim for FAISS)",
                        "created_at": "timestamp",
                        "updated_at": "timestamp"
                    },
                    "indexes": ["product_id", "category", "rating", "discounted_price"]
                },
                
                "reviews": {
                    "description": "Product reviews from users",
                    "fields": {
                        "review_id": "ObjectId",
                        "product_id": "string (foreign key, indexed)",
                        "user_id": "ObjectId (foreign key, indexed)",
                        "rating": "number (1-5)",
                        "title": "string",
                        "text": "string",
                        "sentiment": "POSITIVE/NEGATIVE/NEUTRAL (indexed)",
                        "helpful_count": "number",
                        "verified_purchase": "boolean",
                        "created_at": "timestamp",
                        "updated_at": "timestamp"
                    },
                    "indexes": ["product_id", "user_id", "sentiment", "created_at"]
                },
                
                "recommendations": {
                    "description": "Personalized recommendations for users",
                    "fields": {
                        "recommendation_id": "ObjectId",
                        "user_id": "ObjectId (indexed)",
                        "product_id": "string",
                        "score": "number (0-1)",
                        "reason": "string (category-based, collaborative, trending)",
                        "type": "string (personalized, trending, similar)",
                        "created_at": "timestamp",
                        "clicked": "boolean",
                        "purchased": "boolean"
                    },
                    "indexes": ["user_id", "created_at", "clicked"]
                },
                
                "search_history": {
                    "description": "Track user searches for analytics",
                    "fields": {
                        "search_id": "ObjectId",
                        "user_id": "ObjectId (indexed)",
                        "query": "string",
                        "results_count": "number",
                        "top_result_id": "string",
                        "timestamp": "timestamp"
                    },
                    "indexes": ["user_id", "timestamp"]
                },
                
                "wishlist": {
                    "description": "User wishlists",
                    "fields": {
                        "wishlist_id": "ObjectId",
                        "user_id": "ObjectId (unique, indexed)",
                        "items": [{
                            "product_id": "string",
                            "added_at": "timestamp",
                            "priority": "number (1-5)"
                        }],
                        "created_at": "timestamp",
                        "updated_at": "timestamp"
                    },
                    "indexes": ["user_id"]
                },
                
                "cart": {
                    "description": "Shopping cart items",
                    "fields": {
                        "cart_id": "ObjectId",
                        "user_id": "ObjectId (unique, indexed)",
                        "items": [{
                            "product_id": "string",
                            "quantity": "number",
                            "price": "number",
                            "added_at": "timestamp"
                        }],
                        "total_items": "number",
                        "total_price": "number",
                        "created_at": "timestamp",
                        "updated_at": "timestamp"
                    },
                    "indexes": ["user_id"]
                },
                
                "purchases": {
                    "description": "Purchase history",
                    "fields": {
                        "purchase_id": "ObjectId",
                        "user_id": "ObjectId (indexed)",
                        "items": [{
                            "product_id": "string",
                            "quantity": "number",
                            "price": "number"
                        }],
                        "total_amount": "number",
                        "status": "pending/confirmed/shipped/delivered (indexed)",
                        "order_date": "timestamp",
                        "delivery_date": "timestamp"
                    },
                    "indexes": ["user_id", "status", "order_date"]
                },
                
                "ai_chats": {
                    "description": "AI shopping copilot chat history",
                    "fields": {
                        "chat_id": "ObjectId",
                        "user_id": "ObjectId (indexed)",
                        "messages": [{
                            "role": "user/assistant",
                            "content": "string",
                            "timestamp": "timestamp",
                            "products_referenced": "array of product IDs"
                        }],
                        "created_at": "timestamp",
                        "updated_at": "timestamp",
                        "resolved": "boolean"
                    },
                    "indexes": ["user_id", "created_at"]
                },
                
                "user_behavior": {
                    "description": "Track user interactions for analytics",
                    "fields": {
                        "behavior_id": "ObjectId",
                        "user_id": "ObjectId (indexed)",
                        "action_type": "view/click/add_to_cart/purchase/wishlist (indexed)",
                        "product_id": "string",
                        "session_id": "string",
                        "timestamp": "timestamp"
                    },
                    "indexes": ["user_id", "action_type", "timestamp"]
                }
            }
        }
    }
}

# MongoDB Connection URI (to be set via environment variable)
MONGODB_URI = "mongodb+srv://{username}:{password}@{cluster}.mongodb.net/shopmind_ai?retryWrites=true&w=majority"

# Example connection setup for Python
MONGODB_SETUP = """
from pymongo import MongoClient, ASCENDING, DESCENDING
from datetime import datetime

# Connect to MongoDB
client = MongoClient(MONGODB_URI)
db = client.shopmind_ai

# Create collections with validation
def initialize_database():
    '''Initialize database collections and indexes'''
    
    # Users collection
    if 'users' not in db.list_collection_names():
        db.create_collection('users')
    db.users.create_index([('email', ASCENDING)], unique=True)
    db.users.create_index([('created_at', DESCENDING)])
    
    # Products collection
    if 'products' not in db.list_collection_names():
        db.create_collection('products')
    db.products.create_index([('product_id', ASCENDING)], unique=True)
    db.products.create_index([('category', ASCENDING)])
    db.products.create_index([('rating', DESCENDING)])
    db.products.create_index([('discounted_price', ASCENDING)])
    
    # Reviews collection
    if 'reviews' not in db.list_collection_names():
        db.create_collection('reviews')
    db.reviews.create_index([('product_id', ASCENDING)])
    db.reviews.create_index([('user_id', ASCENDING)])
    db.reviews.create_index([('sentiment', ASCENDING)])
    db.reviews.create_index([('created_at', DESCENDING)])
    
    # Other collections...
    print("✓ Database initialized with collections and indexes")

# Sample document insertion
def insert_sample_user():
    user = {
        'email': 'user@example.com',
        'name': 'John Doe',
        'password_hash': 'hashed_password_here',
        'preferences': {
            'categories': ['Laptops', 'Electronics'],
            'budget_max': 100000,
            'language': 'en'
        },
        'created_at': datetime.now(),
        'is_active': True
    }
    result = db.users.insert_one(user)
    print(f"✓ User created: {result.inserted_id}")
"""

if __name__ == "__main__":
    import json
    print(json.dumps(MONGODB_SCHEMA, indent=2))
