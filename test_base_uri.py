#!/usr/bin/env python
"""Direct MongoDB Atlas Test"""

from pymongo import MongoClient
import os
import re
from dotenv import load_dotenv

load_dotenv('backend/.env')

# Use base URI directly
base_uri = os.getenv('MONGODB_URI', 'mongodb+srv://<db_user>:<db_password>@<cluster>.mongodb.net/')

print('Testing Base URI (no query parameters)')
print(f'URI: {re.sub(r":([^:@/]+)@", r":***@", base_uri)}')
print()

try:
    print('Attempting connection...')
    client = MongoClient(base_uri, serverSelectionTimeoutMS=10000)
    
    print('Pinging admin database...')
    result = client.admin.command('ping')
    
    print('✅ CONNECTION SUCCESSFUL')
    print()
    
    # Get database info
    db = client['shopmind_ai']
    print(f'Database: shopmind_ai')
    
    collections = db.list_collection_names()
    print(f'Collections: {len(collections)}')
    
    if collections:
        for col in collections[:5]:
            count = db[col].estimated_document_count()
            print(f'  - {col}: {count} docs')
    
    client.close()
    
    print()
    print('SUCCESS: MongoDB is accessible with base URI')
    
except Exception as e:
    print(f'❌ Failed: {str(e)[:150]}')
