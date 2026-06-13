#!/usr/bin/env python
"""Simple sync MongoDB connection test"""

import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv('backend/.env')

uri = os.getenv('MONGODB_URI')
db_name = os.getenv('MONGODB_DB_NAME')

print('Testing Sync MongoDB Connection')
print(f'URI: {uri.replace("ShopingAI", "***")}')
print()

try:
    print('Connecting...')
    client = MongoClient(uri, serverSelectionTimeoutMS=10000)
    print('Pinging...')
    client.admin.command('ping')
    print('✅ Sync connection works!')
    
    db = client[db_name]
    collections = db.list_collection_names()
    print(f'✅ Database accessible')
    print(f'Collections: {len(collections)}')
    
    client.close()
    print()
    print('SUCCESS: MongoDB is ready for backend')
except Exception as e:
    print(f'❌ Error: {str(e)[:200]}')
