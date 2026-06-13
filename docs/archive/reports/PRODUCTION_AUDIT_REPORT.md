# ShopMind AI - Production Readiness Audit Report

**Generated:** 2026-06-13T15:50:00.819783

## Overall Status

- **Overall Score:** 59%
- **Components Audited:** 4
- **Issues Found:** 6
- **Fixes Applied:** 0

## Component Scores

- **Project Structure:** 100% (HEALTHY)
- **Environment:** 25% (CRITICAL)
- **Api Coverage:** 90% (HEALTHY)
- **Database:** 20% (CRITICAL)

## Detailed Findings

### Phase: 1 Project Structure

### Phase: 2 Environment

**Issues:**
- Missing dependency: ﻿sentence-transformers
- Missing dependency: faiss-cpu
- Missing dependency: scikit-learn
- Missing dependency: python-dotenv==1.0.1
- Missing dependency: uvicorn[standard]

### Phase: 3 Api Endpoints

### Phase: 4 Mongodb

**Issues:**
- MongoDB connection error: SSL handshake failed: ac-uhqzsqm-shard-00-02.7uzidwv.mongodb.net:27017: [SSL: TLSV1_ALERT_INTERNAL_ERROR] tlsv1 alert internal error (_ssl.c:1028) (configured timeouts: socketTimeoutMS: 20000.0ms, connectTimeoutMS: 20000.0ms),SSL handshake failed: ac-uhqzsqm-shard-00-01.7uzidwv.mongodb.net:27017: [SSL: TLSV1_ALERT_INTERNAL_ERROR] tlsv1 alert internal error (_ssl.c:1028) (configured timeouts: socketTimeoutMS: 20000.0ms, connectTimeoutMS: 20000.0ms),SSL handshake failed: ac-uhqzsqm-shard-00-00.7uzidwv.mongodb.net:27017: [SSL: TLSV1_ALERT_INTERNAL_ERROR] tlsv1 alert internal error (_ssl.c:1028) (configured timeouts: socketTimeoutMS: 20000.0ms, connectTimeoutMS: 20000.0ms), Timeout: 5.0s, Topology Description: <TopologyDescription id: 6a2d2ed495d0f6d4efae3f6d, topology_type: ReplicaSetNoPrimary, servers: [<ServerDescription ('ac-uhqzsqm-shard-00-00.7uzidwv.mongodb.net', 27017) server_type: Unknown, rtt: None, error=AutoReconnect('SSL handshake failed: ac-uhqzsqm-shard-00-00.7uzidwv.mongodb.net:27017: [SSL: TLSV1_ALERT_INTERNAL_ERROR] tlsv1 alert internal error (_ssl.c:1028) (configured timeouts: socketTimeoutMS: 20000.0ms, connectTimeoutMS: 20000.0ms)')>, <ServerDescription ('ac-uhqzsqm-shard-00-01.7uzidwv.mongodb.net', 27017) server_type: Unknown, rtt: None, error=AutoReconnect('SSL handshake failed: ac-uhqzsqm-shard-00-01.7uzidwv.mongodb.net:27017: [SSL: TLSV1_ALERT_INTERNAL_ERROR] tlsv1 alert internal error (_ssl.c:1028) (configured timeouts: socketTimeoutMS: 20000.0ms, connectTimeoutMS: 20000.0ms)')>, <ServerDescription ('ac-uhqzsqm-shard-00-02.7uzidwv.mongodb.net', 27017) server_type: Unknown, rtt: None, error=AutoReconnect('SSL handshake failed: ac-uhqzsqm-shard-00-02.7uzidwv.mongodb.net:27017: [SSL: TLSV1_ALERT_INTERNAL_ERROR] tlsv1 alert internal error (_ssl.c:1028) (configured timeouts: socketTimeoutMS: 20000.0ms, connectTimeoutMS: 20000.0ms)')>]>

