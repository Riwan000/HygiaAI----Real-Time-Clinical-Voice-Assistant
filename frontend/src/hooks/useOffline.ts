/**
 * useOffline Hook
 * 
 * Provides offline/online status and sync capabilities
 */

import { useState, useEffect, useCallback } from 'react';
import { processQueue, getQueueStats, type QueuedRequest } from '../utils/offlineQueue';
import { apiRequest } from '../services/api';

export interface OfflineStatus {
  isOnline: boolean;
  isLocalOnly: boolean;
  queueStats: {
    pending: number;
    processing: number;
    failed: number;
    total: number;
  };
  isSyncing: boolean;
  lastSyncTime: number | null;
}

export function useOffline() {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [isLocalOnly, setIsLocalOnly] = useState(
    localStorage.getItem('hygiaai_local_only') === 'true'
  );
  const [queueStats, setQueueStats] = useState({
    pending: 0,
    processing: 0,
    failed: 0,
    total: 0,
  });
  const [isSyncing, setIsSyncing] = useState(false);
  const [lastSyncTime, setLastSyncTime] = useState<number | null>(
    parseInt(localStorage.getItem('hygiaai_last_sync') || '0') || null
  );

  // Update online status
  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true);
      if (!isLocalOnly) {
        syncQueue();
      }
    };

    const handleOffline = () => {
      setIsOnline(false);
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [isLocalOnly]);

  // Update queue stats periodically
  useEffect(() => {
    const updateStats = async () => {
      const stats = await getQueueStats();
      setQueueStats(stats);
    };

    updateStats();
    const interval = setInterval(updateStats, 5000); // Update every 5 seconds

    return () => clearInterval(interval);
  }, []);

  // Sync queue when coming online
  const syncQueue = useCallback(async () => {
    if (isSyncing || isLocalOnly) return;

    setIsSyncing(true);
    try {
      const result = await processQueue(apiRequest);
      setLastSyncTime(Date.now());
      localStorage.setItem('hygiaai_last_sync', Date.now().toString());
      
      // Update stats after sync
      const stats = await getQueueStats();
      setQueueStats(stats);

      return result;
    } catch (error) {
      console.error('Error syncing queue:', error);
      throw error;
    } finally {
      setIsSyncing(false);
    }
  }, [isSyncing, isLocalOnly]);

  // Toggle local-only mode
  const toggleLocalOnly = useCallback((enabled: boolean) => {
    setIsLocalOnly(enabled);
    localStorage.setItem('hygiaai_local_only', enabled.toString());
  }, []);

  // Manual sync trigger
  const triggerSync = useCallback(async () => {
    if (!isOnline) {
      throw new Error('Cannot sync while offline');
    }
    return await syncQueue();
  }, [isOnline, syncQueue]);

  return {
    isOnline,
    isLocalOnly,
    queueStats,
    isSyncing,
    lastSyncTime,
    syncQueue,
    toggleLocalOnly,
    triggerSync,
  };
}

