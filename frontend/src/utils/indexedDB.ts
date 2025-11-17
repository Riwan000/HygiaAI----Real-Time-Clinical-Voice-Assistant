/**
 * IndexedDB Utilities
 * 
 * Provides a typed interface for IndexedDB operations including
 * storing cases, SOAP notes, knowledge entries, and offline queue items.
 */

const DB_NAME = 'hygiaai_db';
const DB_VERSION = 1;

export type StoreName = 
  | 'cases'
  | 'soap_notes'
  | 'knowledge_entries'
  | 'offline_queue'
  | 'sync_metadata';

interface DBStore {
  cases: IDBObjectStore;
  soap_notes: IDBObjectStore;
  knowledge_entries: IDBObjectStore;
  offline_queue: IDBObjectStore;
  sync_metadata: IDBObjectStore;
}

/**
 * Open IndexedDB database
 */
export function openDB(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);

    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);

    request.onupgradeneeded = (event) => {
      const db = (event.target as IDBOpenDBRequest).result;

      // Create object stores if they don't exist
      if (!db.objectStoreNames.contains('cases')) {
        const casesStore = db.createObjectStore('cases', { keyPath: 'id' });
        casesStore.createIndex('patient_id', 'patient_id', { unique: false });
        casesStore.createIndex('timestamp', 'metadata.timestamp', { unique: false });
      }

      if (!db.objectStoreNames.contains('soap_notes')) {
        const soapStore = db.createObjectStore('soap_notes', { keyPath: 'id' });
        soapStore.createIndex('case_id', 'case_id', { unique: false });
        soapStore.createIndex('patient_id', 'patient_id', { unique: false });
        soapStore.createIndex('generated_at', 'generated_at', { unique: false });
      }

      if (!db.objectStoreNames.contains('knowledge_entries')) {
        const knowledgeStore = db.createObjectStore('knowledge_entries', { keyPath: 'id' });
        knowledgeStore.createIndex('domain', 'domain', { unique: false });
        knowledgeStore.createIndex('source', 'source', { unique: false });
      }

      if (!db.objectStoreNames.contains('offline_queue')) {
        const queueStore = db.createObjectStore('offline_queue', { 
          keyPath: 'id',
          autoIncrement: true 
        });
        queueStore.createIndex('timestamp', 'timestamp', { unique: false });
        queueStore.createIndex('status', 'status', { unique: false });
      }

      if (!db.objectStoreNames.contains('sync_metadata')) {
        const syncStore = db.createObjectStore('sync_metadata', { keyPath: 'key' });
      }
    };
  });
}

/**
 * Generic function to add/update data in a store
 */
export async function putData<T extends { id: string }>(
  storeName: StoreName,
  data: T
): Promise<void> {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const transaction = db.transaction([storeName], 'readwrite');
    const store = transaction.objectStore(storeName);
    const request = store.put(data);

    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve();
  });
}

/**
 * Generic function to get data from a store
 */
export async function getData<T>(
  storeName: StoreName,
  id: string
): Promise<T | undefined> {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const transaction = db.transaction([storeName], 'readonly');
    const store = transaction.objectStore(storeName);
    const request = store.get(id);

    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result as T | undefined);
  });
}

/**
 * Generic function to get all data from a store
 */
export async function getAllData<T>(
  storeName: StoreName,
  indexName?: string,
  query?: IDBValidKey | IDBKeyRange
): Promise<T[]> {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const transaction = db.transaction([storeName], 'readonly');
    const store = transaction.objectStore(storeName);
    const source = indexName ? store.index(indexName) : store;
    const request = query ? source.getAll(query) : source.getAll();

    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result as T[]);
  });
}

/**
 * Generic function to delete data from a store
 */
export async function deleteData(
  storeName: StoreName,
  id: string
): Promise<void> {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const transaction = db.transaction([storeName], 'readwrite');
    const store = transaction.objectStore(storeName);
    const request = store.delete(id);

    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve();
  });
}

/**
 * Clear all data from a store
 */
export async function clearStore(storeName: StoreName): Promise<void> {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const transaction = db.transaction([storeName], 'readwrite');
    const store = transaction.objectStore(storeName);
    const request = store.clear();

    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve();
  });
}

/**
 * Get count of items in a store
 */
export async function getCount(storeName: StoreName): Promise<number> {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const transaction = db.transaction([storeName], 'readonly');
    const store = transaction.objectStore(storeName);
    const request = store.count();

    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
  });
}

/**
 * Delete expired data based on timestamp
 */
export async function deleteExpiredData(
  storeName: StoreName,
  maxAgeMs: number
): Promise<number> {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const transaction = db.transaction([storeName], 'readwrite');
    const store = transaction.objectStore(storeName);
    const request = store.openCursor();
    let deletedCount = 0;
    const cutoffTime = Date.now() - maxAgeMs;

    request.onerror = () => reject(request.error);
    request.onsuccess = (event) => {
      const cursor = (event.target as IDBRequest<IDBCursorWithValue>).result;
      if (cursor) {
        const item = cursor.value;
        const itemTime = item.timestamp || item.metadata?.timestamp || item.generated_at;
        
        if (itemTime && new Date(itemTime).getTime() < cutoffTime) {
          cursor.delete();
          deletedCount++;
        }
        cursor.continue();
      } else {
        resolve(deletedCount);
      }
    };
  });
}

