/**
 * useBackendStatus — polls backend health every 30s
 * and provides status to any component via context
 */

import { useState, useEffect, useCallback } from 'react';
import { getBackendStatus, BackendStatus } from '../services/api';

export interface BackendHealth {
  status: BackendStatus;
  modelsLoaded: boolean;
  totalProducts?: number;
  categories?: number;
  lastChecked?: Date;
}

export function useBackendStatus(intervalMs: number = 30000) {
  const [health, setHealth] = useState<BackendHealth>({
    status: 'loading',
    modelsLoaded: false,
  });

  const check = useCallback(async () => {
    try {
      const result = await getBackendStatus();
      setHealth({
        status: result.status,
        modelsLoaded: result.modelsLoaded,
        totalProducts: result.stats?.total_products,
        categories: result.stats?.categories,
        lastChecked: new Date(),
      });
    } catch {
      setHealth((prev) => ({ ...prev, status: 'offline' }));
    }
  }, []);

  useEffect(() => {
    check();
    const interval = setInterval(check, intervalMs);
    return () => clearInterval(interval);
  }, [check, intervalMs]);

  return health;
}
