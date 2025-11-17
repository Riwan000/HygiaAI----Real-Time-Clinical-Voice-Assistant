/**
 * Offline Queue Manager
 * 
 * Manages a queue of API requests that failed due to network issues.
 * Automatically retries queued requests when connection is restored.
 */

import { putData, getAllData, deleteData, getData } from './indexedDB';
import type { AxiosRequestConfig } from 'axios';

export interface QueuedRequest {
  id: number | string;
  url: string;
  method: string;
  data?: any;
  headers?: Record<string, string>;
  timestamp: number;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  retryCount: number;
  maxRetries: number;
}

const MAX_RETRIES = 3;
const RETRY_DELAY_MS = 1000;

/**
 * Add a request to the offline queue
 */
export async function queueRequest(
  config: AxiosRequestConfig
): Promise<number | string> {
  const queuedRequest: Omit<QueuedRequest, 'id'> = {
    url: config.url || '',
    method: config.method?.toUpperCase() || 'GET',
    data: config.data,
    headers: config.headers as Record<string, string>,
    timestamp: Date.now(),
    status: 'pending',
    retryCount: 0,
    maxRetries: MAX_RETRIES,
  };

  // Store in IndexedDB (id will be auto-generated)
  const db = await import('./indexedDB').then(m => m.openDB());
  return new Promise((resolve, reject) => {
    const transaction = db.transaction(['offline_queue'], 'readwrite');
    const store = transaction.objectStore('offline_queue');
    const request = store.add(queuedRequest);

    request.onerror = () => reject(request.error);
    request.onsuccess = () => {
      const id = request.result;
      resolve(typeof id === 'number' ? id : String(id));
    };
  });
}

/**
 * Get all pending requests from the queue
 */
export async function getPendingRequests(): Promise<QueuedRequest[]> {
  const requests = await getAllData<QueuedRequest>('offline_queue', 'status', 'pending');
  return requests.sort((a, b) => a.timestamp - b.timestamp);
}

/**
 * Update request status
 */
export async function updateRequestStatus(
  id: number | string,
  status: QueuedRequest['status']
): Promise<void> {
  const request = await getData<QueuedRequest>('offline_queue', String(id));
  if (request) {
    request.status = status;
    if (status === 'processing') {
      request.retryCount++;
    }
    await putData('offline_queue', { ...request, id: String(id) });
  }
}

/**
 * Remove completed request from queue
 */
export async function removeRequest(id: number | string): Promise<void> {
  await deleteData('offline_queue', String(id));
}

/**
 * Process queued requests when online
 */
export async function processQueue(
  apiRequest: (config: AxiosRequestConfig) => Promise<any>
): Promise<{ success: number; failed: number }> {
  const pendingRequests = await getPendingRequests();
  let success = 0;
  let failed = 0;

  for (const request of pendingRequests) {
    if (request.retryCount >= request.maxRetries) {
      await updateRequestStatus(request.id, 'failed');
      failed++;
      continue;
    }

    try {
      await updateRequestStatus(request.id, 'processing');

      const config: AxiosRequestConfig = {
        url: request.url,
        method: request.method as any,
        data: request.data,
        headers: request.headers,
      };

      await apiRequest(config);
      
      await updateRequestStatus(request.id, 'completed');
      await removeRequest(request.id);
      success++;
    } catch (error) {
      console.error(`Failed to process queued request ${request.id}:`, error);
      
      if (request.retryCount >= request.maxRetries) {
        await updateRequestStatus(request.id, 'failed');
        failed++;
      } else {
        // Reset to pending for retry
        await updateRequestStatus(request.id, 'pending');
        failed++;
      }
    }

    // Add delay between retries
    if (pendingRequests.length > 1) {
      await new Promise(resolve => setTimeout(resolve, RETRY_DELAY_MS));
    }
  }

  return { success, failed };
}

/**
 * Get queue statistics
 */
export async function getQueueStats(): Promise<{
  pending: number;
  processing: number;
  failed: number;
  total: number;
}> {
  const allRequests = await getAllData<QueuedRequest>('offline_queue');
  
  return {
    pending: allRequests.filter(r => r.status === 'pending').length,
    processing: allRequests.filter(r => r.status === 'processing').length,
    failed: allRequests.filter(r => r.status === 'failed').length,
    total: allRequests.length,
  };
}

/**
 * Clear failed requests
 */
export async function clearFailedRequests(): Promise<number> {
  const allRequests = await getAllData<QueuedRequest>('offline_queue');
  const failedRequests = allRequests.filter(r => r.status === 'failed');
  
  for (const request of failedRequests) {
    await removeRequest(request.id);
  }
  
  return failedRequests.length;
}

