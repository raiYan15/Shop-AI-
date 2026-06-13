#!/usr/bin/env python
"""Test MongoDB Atlas Connection"""

from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError, ConnectionFailure
import os
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv('backend/.env')

uri = os.getenv('MONGODB_URI', 'mongodb+srv://<db_user>:<db_password>@<cluster>.mongodb.net/')
db_name = os.getenv('MONGODB_DB_NAME', 'shopmind_ai')

print('=' * 60)
print('MONGODB ATLAS CONNECTION TEST')
print('=' * 60)
print()

# Mask password in display
display_uri = re.sub(r":([^:@/]+)@", r":***@", uri)
print(f'📍 Cluster URL: {display_uri}')
print(f'📍 Database: {db_name}')
print()

try:
    print('🔌 Connecting to MongoDB Atlas...')
    
    client = MongoClient(
        uri,
        serverSelectionTimeoutMS=10000,
        connectTimeoutMS=10000,
        socketTimeoutMS=10000
    )
    
    # Try to ping the server
    print('⏳ Sending ping command...')
    admin_db = client.admin
    admin_db.command('ping')
    
    print('✅ CONNECTION SUCCESSFUL!')
    print()
    
    # Get server info
    try:
        server_info = client.server_info()
        print(f'MongoDB Version: {server_info.get("version", "N/A")}')
        print(f'Operating System: {server_info.get("os", {}).get("type", "N/A")}')
        print()
    except Exception as e:
        print(f'Could not get server info: {e}')
        print()
    
    # Check database
    db = client[db_name]
    print(f'✅ Database "{db_name}" accessible')
    
    # List collections
    collections = db.list_collection_names()
    print(f'📊 Collections in database: {len(collections)}')
    if collections:
        print()
        for col in collections[:10]:
            try:
                count = db[col].estimated_document_count()
                print(f'   ✓ {col:<30} {count:>8} documents')
            except Exception as e:
                print(f'   ✓ {col:<30} (error counting)')
    else:
        print('   (No collections yet)')
    
    print()
    print('=' * 60)
    print('✅ MONGODB ATLAS IS WORKING!')
    print('=' * 60)
    
    client.close()
    
except ServerSelectionTimeoutError as e:
    print('❌ CONNECTION FAILED - Server Selection Timeout')
    print()
    print('Possible causes:')
    print('  • Network firewall blocking connection to MongoDB')
    print('  • IP address not whitelisted in MongoDB Atlas')
    print('  • Cluster is not running')
    print('  • DNS resolution issue')
    print()
    print(f'Error details: {str(e)[:300]}')
    
except ConnectionFailure as e:
    print('❌ CONNECTION FAILED')
    print(f'Error: {str(e)[:300]}')
    
except Exception as e:
    print(f'❌ ERROR: {type(e).__name__}')
    print(f'Details: {str(e)[:300]}')

print()
