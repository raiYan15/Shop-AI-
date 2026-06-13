#!/usr/bin/env python
"""Test MongoDB Connection with SSL Workarounds"""

from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError, ConnectionFailure
import ssl
import os
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv('backend/.env')

uri = os.getenv('MONGODB_URI', 'mongodb+srv://<db_user>:<db_password>@<cluster>.mongodb.net/')
db_name = os.getenv('MONGODB_DB_NAME', 'shopmind_ai')

display_uri = re.sub(r":([^:@/]+)@", r":***@", uri)

print('=' * 70)
print('MONGODB CONNECTION TEST WITH SSL WORKAROUNDS')
print('=' * 70)
print()
print(f'📍 Cluster: {display_uri}')
print(f'📍 Database: {db_name}')
print()

# Test 1: Direct connection
print('TEST 1: Direct Connection (Default)')
print('-' * 70)
try:
    client = MongoClient(uri, serverSelectionTimeoutMS=10000)
    admin_db = client.admin
    admin_db.command('ping')
    print('✅ SUCCESS - Direct connection works')
    client.close()
except Exception as e:
    print(f'❌ FAILED - {str(e)[:150]}')
print()

# Test 2: With SSL verification disabled
print('TEST 2: SSL Verification Disabled')
print('-' * 70)
try:
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    client = MongoClient(
        uri,
        serverSelectionTimeoutMS=10000,
        ssl_context=ssl_context
    )
    admin_db = client.admin
    admin_db.command('ping')
    print('✅ SUCCESS - Connection works with SSL verification disabled')
    
    # Try to get more info
    db = client[db_name]
    collections = db.list_collection_names()
    print(f'   Database accessible: ✅')
    print(f'   Collections: {len(collections)}')
    
    client.close()
except Exception as e:
    print(f'❌ FAILED - {str(e)[:150]}')
print()

# Test 3: Using tlsAllowInvalidCertificates parameter
print('TEST 3: Using tlsAllowInvalidCertificates=True')
print('-' * 70)
try:
    client = MongoClient(
        uri,
        serverSelectionTimeoutMS=10000,
        tlsAllowInvalidCertificates=True
    )
    admin_db = client.admin
    admin_db.command('ping')
    print('✅ SUCCESS - Connection works with tlsAllowInvalidCertificates=True')
    
    # Try to get more info
    db = client[db_name]
    collections = db.list_collection_names()
    print(f'   Database accessible: ✅')
    print(f'   Collections: {len(collections)}')
    
    if collections:
        print()
        print('   Collections in database:')
        for col in collections[:10]:
            try:
                count = db[col].estimated_document_count()
                print(f'      ✓ {col:<30} {count:>8} documents')
            except Exception as e:
                print(f'      ✓ {col:<30} (error counting)')
    
    client.close()
except Exception as e:
    print(f'❌ FAILED - {str(e)[:150]}')
print()

print('=' * 70)
print('RECOMMENDATION')
print('=' * 70)
print()
print('If TEST 3 works, add this to backend/.env:')
print('  tlsAllowInvalidCertificates=True')
print()
print('Or update backend/services/db.py to include:')
print('  client = MongoClient(uri, tlsAllowInvalidCertificates=True)')
print()
