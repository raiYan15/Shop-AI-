#!/usr/bin/env python
"""Test MongoDB with URI query parameters for SSL"""

from pymongo import MongoClient
import os
import re
from dotenv import load_dotenv

load_dotenv('backend/.env')

# Original URI (env-driven)
base_uri = os.getenv('MONGODB_URI', 'mongodb+srv://<db_user>:<db_password>@<cluster>.mongodb.net/')

# URI with SSL parameters as query string
# Note: MongoDB Connection String options can be passed as query parameters
uris_to_test = [
    {
        'name': 'Test 1: Base URI',
        'uri': base_uri,
        'params': {}
    },
    {
        'name': 'Test 2: With tlsAllowInvalidCertificates',
        'uri': base_uri,
        'params': {'tlsAllowInvalidCertificates': True}
    },
    {
        'name': 'Test 3: With retryWrites',
        'uri': base_uri,
        'params': {'tlsAllowInvalidCertificates': True, 'retryWrites': True}
    },
]

print('=' * 70)
print('MONGODB URI PARAMETER TESTING')
print('=' * 70)
print()

for test in uris_to_test:
    print(f"{test['name']}")
    print('-' * 70)
    
    try:
        print(f"Connecting...")
        client = MongoClient(
            test['uri'],
            serverSelectionTimeoutMS=10000,
            connectTimeoutMS=10000,
            **test['params']
        )
        
        print(f"Sending ping...")
        client.admin.command('ping')
        
        print(f"✅ SUCCESS")
        
        # Check database
        db = client['shopmind_ai']
        collections = db.list_collection_names()
        print(f"   Collections: {len(collections)}")
        
        client.close()
        
    except Exception as e:
        error_msg = str(e)
        if 'SSL' in error_msg or 'ssl' in error_msg or 'TLS' in error_msg or 'tls' in error_msg:
            print(f"❌ SSL/TLS ERROR: {error_msg[:100]}")
        else:
            print(f"❌ CONNECTION ERROR: {error_msg[:100]}")
    
    print()

print('=' * 70)
print('ALTERNATIVE: Try with URI query string')
print('=' * 70)
print()

# Try with URI query string parameter
uri_with_params = base_uri + "?tlsAllowInvalidCertificates=true"
print(f"URI: {re.sub(r':([^:@/]+)@', r':***@', uri_with_params)}")
print()

try:
    client = MongoClient(uri_with_params, serverSelectionTimeoutMS=10000)
    client.admin.command('ping')
    print("✅ SUCCESS with URI query parameter")
    client.close()
except Exception as e:
    print(f"❌ FAILED: {str(e)[:150]}")

print()
