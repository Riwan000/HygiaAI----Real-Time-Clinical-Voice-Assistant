/**
 * Settings Page
 * 
 * Application settings including offline mode, sync controls, and data management
 */

import { useState, useEffect } from 'react';
import { Breadcrumbs } from '../components/Breadcrumbs';
import { useOffline } from '../hooks/useOffline';
import { clearFailedRequests, getQueueStats } from '../utils/offlineQueue';
import { deleteExpiredData, getCount } from '../utils/indexedDB';
import { 
  SignalSlashIcon, 
  WifiIcon,
  ArrowPathIcon,
  TrashIcon,
  CheckCircleIcon,
} from '@heroicons/react/24/outline';
import { clsx } from '../utils/clsx';

export function Settings() {
  const { 
    isOnline, 
    isLocalOnly, 
    queueStats, 
    isSyncing, 
    lastSyncTime,
    toggleLocalOnly,
    triggerSync,
  } = useOffline();

  const [storageStats, setStorageStats] = useState({
    cases: 0,
    soap_notes: 0,
    knowledge_entries: 0,
    offline_queue: 0,
  });
  const [isClearing, setIsClearing] = useState(false);
  const [clearMessage, setClearMessage] = useState<string | null>(null);

  useEffect(() => {
    const updateStats = async () => {
      try {
        const [cases, soap, knowledge, queue] = await Promise.all([
          getCount('cases'),
          getCount('soap_notes'),
          getCount('knowledge_entries'),
          getCount('offline_queue'),
        ]);
        setStorageStats({ cases, soap_notes: soap, knowledge_entries: knowledge, offline_queue: queue });
      } catch (error) {
        console.error('Error fetching storage stats:', error);
      }
    };
    updateStats();
    const interval = setInterval(updateStats, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleClearFailed = async () => {
    setIsClearing(true);
    setClearMessage(null);
    try {
      const count = await clearFailedRequests();
      setClearMessage(`Cleared ${count} failed request(s)`);
      const stats = await getQueueStats();
      setStorageStats(prev => ({ ...prev, offline_queue: stats.total }));
    } catch (error) {
      setClearMessage('Error clearing failed requests');
      console.error(error);
    } finally {
      setIsClearing(false);
    }
  };

  const handleClearExpired = async () => {
    setIsClearing(true);
    setClearMessage(null);
    try {
      const maxAge = 30 * 24 * 60 * 60 * 1000; // 30 days
      const deleted = await Promise.all([
        deleteExpiredData('cases', maxAge),
        deleteExpiredData('soap_notes', maxAge),
        deleteExpiredData('knowledge_entries', maxAge),
      ]);
      const totalDeleted = deleted.reduce((sum, count) => sum + count, 0);
      setClearMessage(`Cleared ${totalDeleted} expired item(s)`);
      
      // Update stats
      const [cases, soap, knowledge] = await Promise.all([
        getCount('cases'),
        getCount('soap_notes'),
        getCount('knowledge_entries'),
      ]);
      setStorageStats({ ...storageStats, cases, soap_notes: soap, knowledge_entries: knowledge });
    } catch (error) {
      setClearMessage('Error clearing expired data');
      console.error(error);
    } finally {
      setIsClearing(false);
    }
  };

  const formatLastSync = (timestamp: number | null) => {
    if (!timestamp) return 'Never';
    const diff = Date.now() - timestamp;
    const minutes = Math.floor(diff / 60000);
    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes} minute(s) ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours} hour(s) ago`;
    const days = Math.floor(hours / 24);
    return `${days} day(s) ago`;
  };

  return (
    <div>
      <Breadcrumbs items={[{ name: 'Settings' }]} />
      <h1 className="text-3xl font-bold text-[#1E3A8A] dark:text-white mb-6 font-heading">
        Settings
      </h1>

      <div className="space-y-6">
        {/* Offline Mode Settings */}
        <div className="bg-white dark:bg-[#1E293B] rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
          <h2 className="text-xl font-semibold text-[#1E3A8A] dark:text-white mb-4">
            Offline Mode
          </h2>

          <div className="space-y-4">
            {/* Local-Only Mode Toggle */}
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <label className="text-sm font-medium text-gray-900 dark:text-white">
                  Local-Only Mode
                </label>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                  Disable all network requests. All data will be stored locally only.
                </p>
              </div>
              <button
                onClick={() => toggleLocalOnly(!isLocalOnly)}
                className={clsx(
                  'relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-[#2563EB] focus:ring-offset-2',
                  isLocalOnly ? 'bg-[#2563EB]' : 'bg-gray-200 dark:bg-gray-700'
                )}
                aria-label="Toggle local-only mode"
              >
                <span
                  className={clsx(
                    'inline-block h-4 w-4 transform rounded-full bg-white transition-transform',
                    isLocalOnly ? 'translate-x-6' : 'translate-x-1'
                  )}
                />
              </button>
            </div>

            {/* Connection Status */}
            <div className="flex items-center justify-between pt-4 border-t border-gray-200 dark:border-gray-700">
              <div className="flex items-center space-x-2">
                {isOnline ? (
                  <WifiIcon className="h-5 w-5 text-green-500" />
                ) : (
                  <SignalSlashIcon className="h-5 w-5 text-red-500" />
                )}
                <span className="text-sm font-medium text-gray-900 dark:text-white">
                  {isOnline ? 'Connected' : 'Disconnected'}
                </span>
              </div>
            </div>

            {/* Sync Status */}
            {!isLocalOnly && (
              <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-900 dark:text-white">
                    Last Sync
                  </span>
                  <span className="text-sm text-gray-500 dark:text-gray-400">
                    {formatLastSync(lastSyncTime)}
                  </span>
                </div>
                <button
                  onClick={triggerSync}
                  disabled={!isOnline || isSyncing}
                  className={clsx(
                    'flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors',
                    isOnline && !isSyncing
                      ? 'bg-[#2563EB] text-white hover:bg-[#1E40AF]'
                      : 'bg-gray-200 dark:bg-gray-700 text-gray-400 cursor-not-allowed'
                  )}
                >
                  <ArrowPathIcon className={clsx('h-4 w-4', isSyncing && 'animate-spin')} />
                  <span>{isSyncing ? 'Syncing...' : 'Sync Now'}</span>
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Queue Status */}
        {queueStats.total > 0 && (
          <div className="bg-white dark:bg-[#1E293B] rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
            <h2 className="text-xl font-semibold text-[#1E3A8A] dark:text-white mb-4">
              Offline Queue
            </h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
              <div>
                <div className="text-2xl font-bold text-gray-900 dark:text-white">
                  {queueStats.pending}
                </div>
                <div className="text-sm text-gray-500 dark:text-gray-400">Pending</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-yellow-600 dark:text-yellow-400">
                  {queueStats.processing}
                </div>
                <div className="text-sm text-gray-500 dark:text-gray-400">Processing</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-red-600 dark:text-red-400">
                  {queueStats.failed}
                </div>
                <div className="text-sm text-gray-500 dark:text-gray-400">Failed</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-gray-900 dark:text-white">
                  {queueStats.total}
                </div>
                <div className="text-sm text-gray-500 dark:text-gray-400">Total</div>
              </div>
            </div>
            {queueStats.failed > 0 && (
              <button
                onClick={handleClearFailed}
                disabled={isClearing}
                className="flex items-center space-x-2 px-4 py-2 rounded-lg bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-200 hover:bg-red-200 dark:hover:bg-red-900/50 transition-colors text-sm font-medium"
              >
                <TrashIcon className="h-4 w-4" />
                <span>Clear Failed Requests</span>
              </button>
            )}
          </div>
        )}

        {/* Storage Management */}
        <div className="bg-white dark:bg-[#1E293B] rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
          <h2 className="text-xl font-semibold text-[#1E3A8A] dark:text-white mb-4">
            Local Storage
          </h2>
          <div className="space-y-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <div className="text-2xl font-bold text-gray-900 dark:text-white">
                  {storageStats.cases}
                </div>
                <div className="text-sm text-gray-500 dark:text-gray-400">Cases</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-gray-900 dark:text-white">
                  {storageStats.soap_notes}
                </div>
                <div className="text-sm text-gray-500 dark:text-gray-400">SOAP Notes</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-gray-900 dark:text-white">
                  {storageStats.knowledge_entries}
                </div>
                <div className="text-sm text-gray-500 dark:text-gray-400">Knowledge</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-gray-900 dark:text-white">
                  {storageStats.offline_queue}
                </div>
                <div className="text-sm text-gray-500 dark:text-gray-400">Queued</div>
              </div>
            </div>

            <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
              <button
                onClick={handleClearExpired}
                disabled={isClearing}
                className="flex items-center space-x-2 px-4 py-2 rounded-lg bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors text-sm font-medium"
              >
                <TrashIcon className="h-4 w-4" />
                <span>{isClearing ? 'Clearing...' : 'Clear Expired Data (30+ days)'}</span>
              </button>
            </div>

            {clearMessage && (
              <div className="flex items-center space-x-2 text-sm text-green-600 dark:text-green-400">
                <CheckCircleIcon className="h-5 w-5" />
                <span>{clearMessage}</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
