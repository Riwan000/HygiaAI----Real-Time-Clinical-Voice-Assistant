import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import './index.css';
import App from './App.tsx';
import { registerServiceWorker } from './utils/serviceWorker';

const rootElement = document.getElementById('root');

if (!rootElement) {
  throw new Error('Root element not found');
}

// Add a test to see if React is working
console.log('React is loading...');
console.log('Root element:', rootElement);

// Debug: Check for multiple React instances
if (typeof window !== 'undefined') {
  const reactVersions = new Set();
  // This will help identify if there are multiple React instances
  console.log('React version check:', {
    react: typeof require !== 'undefined' ? require('react')?.version : 'N/A',
    windowReact: (window as any).React?.version || 'N/A',
  });
}

// Register service worker for offline support (non-blocking)
registerServiceWorker().then((registration) => {
  if (registration) {
    console.log('Service worker registered:', registration);
    
    // Check for updates
    registration.addEventListener('updatefound', () => {
      const newWorker = registration.installing;
      if (newWorker) {
        newWorker.addEventListener('statechange', () => {
          if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
            // New service worker available
            console.log('New service worker available');
            // Optionally prompt user to refresh
            if (confirm('A new version is available. Refresh to update?')) {
              window.location.reload();
            }
          }
        });
      }
    });
  }
}).catch((error) => {
  console.warn('Service worker registration failed (non-critical):', error);
  // Don't block app if service worker fails
});

try {
  createRoot(rootElement).render(
    <StrictMode>
      <App />
    </StrictMode>
  );
  console.log('React app rendered successfully');
} catch (error) {
  console.error('Error rendering React app:', error);
  rootElement.innerHTML = `
    <div style="padding: 20px; color: red;">
      <h1>Error rendering app</h1>
      <pre>${String(error)}</pre>
    </div>
  `;
}

