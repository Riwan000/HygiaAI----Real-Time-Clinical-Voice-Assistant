/**
 * Service Worker Registration
 * 
 * Handles service worker registration and update notifications
 */

export async function registerServiceWorker(): Promise<ServiceWorkerRegistration | null> {
  if ('serviceWorker' in navigator) {
    try {
      // Use a more compatible registration approach
      const registration = await navigator.serviceWorker.register('/sw.js', {
        scope: '/',
        updateViaCache: 'none',
      });

      // Check for updates periodically
      setInterval(() => {
        registration.update();
      }, 60 * 60 * 1000); // Check every hour

      // Handle updates
      registration.addEventListener('updatefound', () => {
        const newWorker = registration.installing;
        if (newWorker) {
          newWorker.addEventListener('statechange', () => {
            if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
              // New service worker available, prompt user to refresh
              if (confirm('A new version is available. Refresh to update?')) {
                window.location.reload();
              }
            }
          });
        }
      });

      return registration;
    } catch (error) {
      console.error('Service worker registration failed:', error);
      return null;
    }
  }
  return null;
}

/**
 * Unregister service worker (for development/testing)
 */
export async function unregisterServiceWorker(): Promise<boolean> {
  if ('serviceWorker' in navigator) {
    try {
      const registration = await navigator.serviceWorker.ready;
      const unregistered = await registration.unregister();
      return unregistered;
    } catch (error) {
      console.error('Service worker unregistration failed:', error);
      return false;
    }
  }
  return false;
}

