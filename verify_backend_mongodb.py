#!/usr/bin/env python
"""Verify Complete MongoDB Setup and Data Status"""

import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment
env_path = Path('backend/.env')
load_dotenv(env_path)

# Now import backend modules
import sys
sys.path.insert(0, 'backend')

from services.db import (
    get_async_client, 
    get_sync_db,
    ping_mongodb,
    ensure_indexes,
    MONGODB_URI,
    MONGODB_DB_NAME
)

display_uri = MONGODB_URI.replace('ShopingAI', '***')

async def verify_setup():
    print('=' * 70)
    print('BACKEND MONGODB VERIFICATION')
    print('=' * 70)
    print()
    print(f'📍 URI: {display_uri}')
    print(f'📍 Database: {MONGODB_DB_NAME}')
    print()
    
    # Test async connection
    print('1️⃣  Testing Async Connection (Motor)...')
    try:
        result = await ping_mongodb()
        if result:
            print('   ✅ Async connection works')
        else:
            print('   ❌ Async connection failed')
            return False
    except Exception as e:
        print(f'   ❌ Error: {e}')
        return False
    print()
    
    # Test sync connection
    print('2️⃣  Testing Sync Connection (PyMongo)...')
    try:
        db = get_sync_db()
        db.command('ping')
        print('   ✅ Sync connection works')
    except Exception as e:
        print(f'   ❌ Error: {e}')
        return False
    print()
    
    # Ensure indexes
    print('3️⃣  Creating Indexes...')
    try:
        ensure_indexes()
        print('   ✅ Indexes created successfully')
    except Exception as e:
        print(f'   ⚠️  Index creation: {e}')
    print()
    
    # Check collections
    print('4️⃣  Checking Collections...')
    try:
        db = get_sync_db()
        collections = db.list_collection_names()
        print(f'   Found {len(collections)} collections:')
        if collections:
            for col in collections:
                count = db[col].estimated_document_count()
                print(f'      ✓ {col:<25} {count:>8} documents')
        else:
            print('      (No collections yet - will be created on first use)')
    except Exception as e:
        print(f'   ❌ Error: {e}')
    print()
    
    print('=' * 70)
    print('✅ BACKEND MONGODB SETUP VERIFIED')
    print('=' * 70)
    print()
    print('Status: READY FOR BACKEND START')
    print()
    print('Next steps:')
    print('  1. cd backend')
    print('  2. python -m uvicorn main_api:app --reload --host 0.0.0.0 --port 8000')
    print()
    
    return True

# Run async verification
if __name__ == '__main__':
    try:
        success = asyncio.run(verify_setup())
        exit(0 if success else 1)
    except Exception as e:
        print(f'Fatal error: {e}')
        exit(1)
