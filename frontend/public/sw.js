/**
 * Service Worker for HygiaAI
 * Handles offline caching and asset management
 */

// Version-based cache names - update this version when deploying new changes
const APP_VERSION = 'v2.0.0';
const CACHE_NAME = `hygiaai-${APP_VERSION}`;
const STATIC_CACHE = `hygiaai-static-${APP_VERSION}`;
const API_CACHE = `hygiaai-api-${APP_VERSION}`;

// Assets to cache on install
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/manifest.json',
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
  console.log('[Service Worker] Installing...', APP_VERSION);
  
  event.waitUntil(
    caches.open(STATIC_CACHE).then((cache) => {
      console.log('[Service Worker] Caching static assets');
      return cache.addAll(STATIC_ASSETS);
    })
  );
  
  // Force activation of new service worker
  self.skipWaiting();
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('[Service Worker] Activating...', APP_VERSION);
  
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((name) => !name.includes(APP_VERSION))
          .map((name) => {
            console.log('[Service Worker] Deleting old cache:', name);
            return caches.delete(name);
          })
      );
    }).then(() => {
      // Take control of all pages immediately
      return self.clients.claim();
    })
  );
});

// Fetch event - serve from cache, fallback to network
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);
  
  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }
  
  // Skip cross-origin requests
  if (url.origin !== location.origin) {
    return;
  }
  
  // Network-first strategy for API calls
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(request)
        .then((response) => {
          // Only cache successful responses
          if (response.ok) {
            caches.open(API_CACHE).then((cache) => {
              cache.put(request, response.clone());
            });
          }
          return response;
        })
        .catch(() => {
          // Network failed, try cache
          return caches.match(request).then((cachedResponse) => {
            if (cachedResponse) {
              return cachedResponse;
            }
            return new Response(
              JSON.stringify({ error: 'Offline', message: 'No cached data available' }),
              {
                status: 503,
                headers: { 'Content-Type': 'application/json' },
              }
            );
          });
        })
    );
    return;
  }
  
  // HTML files - always fetch fresh (no cache)
  if (request.headers.get('accept')?.includes('text/html') || url.pathname === '/' || url.pathname.endsWith('.html')) {
    event.respondWith(
      fetch(request)
        .then((response) => {
          // Don't cache HTML files
          return response;
        })
        .catch(() => {
          // Fallback to cache only if network fails
          return caches.match(request);
        })
    );
    return;
  }
  
  // Service worker file - always fetch fresh
  if (url.pathname === '/sw.js') {
    event.respondWith(fetch(request));
    return;
  }
  
  // Static assets - CacheFirst strategy with version check
  event.respondWith(
    caches.match(request).then((cachedResponse) => {
      if (cachedResponse) {
        // Check if cached version is still valid
        return cachedResponse;
      }
      
      // Not in cache, fetch from network
      return fetch(request).then((response) => {
        // Don't cache non-successful responses
        if (!response.ok) {
          return response;
        }
        
        const responseToCache = response.clone();
        caches.open(STATIC_CACHE).then((cache) => {
          cache.put(request, responseToCache);
        });
        
        return response;
      });
    })
  );
});

// Background sync for offline actions
self.addEventListener('sync', (event) => {
  console.log('[Service Worker] Background sync triggered');
  
  if (event.tag === 'sync-queue') {
    event.waitUntil(
      // Sync queued requests
      Promise.resolve()
    );
  }
});

// Message handler for cache management
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
  
  if (event.data && event.data.type === 'CACHE_URLS') {
    event.waitUntil(
      caches.open(STATIC_CACHE).then((cache) => {
        return cache.addAll(event.data.urls);
      })
    );
  }
  
  if (event.data && event.data.type === 'CLEAR_CACHE') {
    event.waitUntil(
      caches.keys().then((cacheNames) => {
        return Promise.all(
          cacheNames.map((name) => caches.delete(name))
        );
      })
    );
  }
});
