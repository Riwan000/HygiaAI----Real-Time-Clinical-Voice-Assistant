/**
 * Offline Status Badge Component
 * 
 * Displays current online/offline status and sync information
 */

import { useEffect, useState } from 'react';
import { 
  WifiIcon, 
  SignalSlashIcon, 
  ArrowPathIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline';
import { useOffline } from '../hooks/useOffline';
import { clsx } from '../utils/clsx';

export function OfflineStatusBadge() {
  const { isOnline, isLocalOnly, queueStats, isSyncing, lastSyncTime } = useOffline();
  const [showDetails, setShowDetails] = useState(false);

  const formatLastSync = (timestamp: number | null) => {
    if (!timestamp) return 'Never';
    const diff = Date.now() - timestamp;
    const minutes = Math.floor(diff / 60000);
    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    return `${days}d ago`;
  };

  if (isLocalOnly) {
    return (
      <div className="relative">
        <button
          onClick={() => setShowDetails(!showDetails)}
          className="flex items-center space-x-1.5 px-2.5 py-1.5 rounded-lg bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-200 text-xs font-medium hover:bg-yellow-200 dark:hover:bg-yellow-900/50 transition-colors focus:outline-none focus:ring-2 focus:ring-yellow-500 focus:ring-offset-2"
          aria-label="Local-only mode enabled"
          aria-expanded={showDetails}
          role="status"
          aria-live="polite"
        >
          <SignalSlashIcon className="h-4 w-4" aria-hidden="true" />
          <span>Local Only</span>
        </button>
      </div>
    );
  }

  if (!isOnline) {
    return (
      <div className="relative">
        <button
          onClick={() => setShowDetails(!showDetails)}
          className="flex items-center space-x-1.5 px-2.5 py-1.5 rounded-lg bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-200 text-xs font-medium hover:bg-red-200 dark:hover:bg-red-900/50 transition-colors focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2"
          aria-label={`Offline. ${queueStats.pending > 0 ? `${queueStats.pending} requests pending` : 'Requests will be queued'}`}
          aria-expanded={showDetails}
          role="status"
          aria-live="polite"
        >
          <SignalSlashIcon className="h-4 w-4" aria-hidden="true" />
          <span>Offline</span>
          {queueStats.pending > 0 && (
            <span className="ml-1 px-1.5 py-0.5 rounded-full bg-red-200 dark:bg-red-800 text-red-900 dark:text-red-100 text-xs font-bold" aria-label={`${queueStats.pending} pending requests`}>
              {queueStats.pending}
            </span>
          )}
        </button>

        {showDetails && (
          <div className="absolute right-0 mt-2 w-64 rounded-lg bg-white dark:bg-[#1E293B] shadow-lg border border-gray-200 dark:border-gray-700 p-4 z-50">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-900 dark:text-white">
                  Offline Queue
                </span>
                <button
                  onClick={() => setShowDetails(false)}
                  className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 focus:outline-none focus:ring-2 focus:ring-[#2563EB] focus:ring-offset-2 rounded"
                  aria-label="Close offline status details"
                >
                  ×
                </button>
              </div>
              <div className="space-y-1 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Pending:</span>
                  <span className="font-medium text-gray-900 dark:text-white">
                    {queueStats.pending}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Failed:</span>
                  <span className="font-medium text-red-600 dark:text-red-400">
                    {queueStats.failed}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Total:</span>
                  <span className="font-medium text-gray-900 dark:text-white">
                    {queueStats.total}
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="relative">
      <button
        onClick={() => setShowDetails(!showDetails)}
        className={clsx(
          'flex items-center space-x-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-[#2563EB] focus:ring-offset-2',
          isSyncing
            ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-200'
            : queueStats.pending > 0
            ? 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-200'
            : 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-200'
        )}
        aria-label={isSyncing ? 'Syncing...' : queueStats.pending > 0 ? `Online. ${queueStats.pending} requests pending sync` : 'Online'}
        aria-expanded={showDetails}
        role="status"
        aria-live="polite"
      >
        {isSyncing ? (
          <ArrowPathIcon className="h-4 w-4 animate-spin" aria-hidden="true" />
        ) : (
          <WifiIcon className="h-4 w-4" aria-hidden="true" />
        )}
        <span>{isSyncing ? 'Syncing...' : 'Online'}</span>
        {queueStats.pending > 0 && !isSyncing && (
          <span className="ml-1 px-1.5 py-0.5 rounded-full bg-yellow-200 dark:bg-yellow-800 text-yellow-900 dark:text-yellow-100 text-xs font-bold" aria-label={`${queueStats.pending} pending requests`}>
            {queueStats.pending}
          </span>
        )}
      </button>

      {showDetails && (
        <div className="absolute right-0 mt-2 w-64 rounded-lg bg-white dark:bg-[#1E293B] shadow-lg border border-gray-200 dark:border-gray-700 p-4 z-50">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-900 dark:text-white">
                Connection Status
              </span>
              <button
                onClick={() => setShowDetails(false)}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 focus:outline-none focus:ring-2 focus:ring-[#2563EB] focus:ring-offset-2 rounded"
                aria-label="Close connection status details"
              >
                ×
              </button>
            </div>

            <div className="space-y-2">
              <div className="flex items-center space-x-2">
                {isOnline ? (
                  <CheckCircleIcon className="h-5 w-5 text-green-500" aria-hidden="true" />
                ) : (
                  <ExclamationTriangleIcon className="h-5 w-5 text-red-500" aria-hidden="true" />
                )}
                <span className="text-sm text-gray-700 dark:text-gray-300">
                  {isOnline ? 'Connected' : 'Disconnected'}
                </span>
              </div>

              {lastSyncTime && (
                <div className="text-xs text-gray-500 dark:text-gray-400">
                  Last sync: {formatLastSync(lastSyncTime)}
                </div>
              )}

              {queueStats.total > 0 && (
                <div className="pt-2 border-t border-gray-200 dark:border-gray-700">
                  <div className="text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Queue Status
                  </div>
                  <div className="space-y-1 text-xs">
                    <div className="flex justify-between">
                      <span className="text-gray-600 dark:text-gray-400">Pending:</span>
                      <span className="font-medium text-gray-900 dark:text-white">
                        {queueStats.pending}
                      </span>
                    </div>
                    {queueStats.failed > 0 && (
                      <div className="flex justify-between">
                        <span className="text-gray-600 dark:text-gray-400">Failed:</span>
                        <span className="font-medium text-red-600 dark:text-red-400">
                          {queueStats.failed}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

