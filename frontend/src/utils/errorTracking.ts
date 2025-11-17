/**
 * Error Tracking with Sentry (optional)
 * Provides error tracking and monitoring capabilities
 */

export interface ErrorTrackingConfig {
  dsn?: string;
  environment?: string;
  release?: string;
  enabled?: boolean;
}

let errorTrackingEnabled = false;
let sentryInitialized = false;

/**
 * Initialize error tracking
 */
export async function initErrorTracking(config?: ErrorTrackingConfig) {
  // Only run in browser environment
  if (typeof window === 'undefined') {
    return;
  }

  const dsn = config?.dsn || import.meta.env.VITE_SENTRY_DSN;
  const enabled = config?.enabled ?? (dsn && dsn.length > 0);

  if (!enabled) {
    return;
  }

  errorTrackingEnabled = true;

  // Dynamically import Sentry to avoid including it in bundle if not configured
  // Only attempt import if DSN is provided
  if (dsn && dsn.length > 0) {
    try {
      // Import from stub module (which will use real module if available)
      const SentryModule = await import('@sentry/react');
      
      // Check if it's a real implementation (stub functions are empty, real ones have code)
      const initFunction = SentryModule?.init?.toString() || '';
      const isRealImplementation = initFunction.length > 50; // Stub is just "() => {}"
      
      if (SentryModule && SentryModule.init && isRealImplementation) {
        const { init, browserTracingIntegration, replayIntegration, captureException, captureMessage, setUser } = SentryModule;
        
        init({
          dsn,
          environment: config?.environment || import.meta.env.MODE || 'production',
          release: config?.release || import.meta.env.VITE_APP_VERSION || '1.0.0',
          integrations: [
            browserTracingIntegration(),
            replayIntegration({
              maskAllText: true,
              blockAllMedia: true,
            }),
          ],
          tracesSampleRate: 1.0,
          replaysSessionSampleRate: 0.1,
          replaysOnErrorSampleRate: 1.0,
        });

        // Store functions for later use
        (window as any).__sentry = SentryModule;
        sentryInitialized = true;
        console.log('Error tracking initialized');
      } else {
        // Stub module loaded, Sentry not actually installed
        console.warn('Sentry not installed, error tracking disabled');
        errorTrackingEnabled = false;
      }
    } catch (error) {
      // Sentry not available, continue without it
      console.warn('Sentry not available, error tracking disabled');
      errorTrackingEnabled = false;
    }
  } else {
    // No DSN provided, disable error tracking
    errorTrackingEnabled = false;
  }
}

/**
 * Capture an error
 */
export function captureError(error: Error, context?: Record<string, any>) {
  if (!errorTrackingEnabled) {
    console.error('Error (tracking disabled):', error, context);
    return;
  }

  if (sentryInitialized) {
    // Use cached Sentry module if available
    const Sentry = (window as any).__sentry;
    if (Sentry && Sentry.captureException) {
      Sentry.captureException(error, {
        contexts: {
          custom: context || {},
        },
      });
    } else {
      // Fallback to dynamic import
      import('@sentry/react').then((SentryModule) => {
        if (SentryModule && SentryModule.captureException) {
          SentryModule.captureException(error, {
            contexts: {
              custom: context || {},
            },
          });
        }
      }).catch(() => {
        console.error('Error:', error, context);
      });
    }
  } else {
    console.error('Error:', error, context);
  }
}

/**
 * Capture a message
 */
export function captureMessage(message: string, level: 'info' | 'warning' | 'error' = 'info') {
  if (!errorTrackingEnabled) {
    console.log(`[${level.toUpperCase()}]`, message);
    return;
  }

  if (sentryInitialized) {
    const Sentry = (window as any).__sentry;
    if (Sentry && Sentry.captureMessage) {
      Sentry.captureMessage(message, level);
    } else {
      import('@sentry/react').then((SentryModule) => {
        if (SentryModule && SentryModule.captureMessage) {
          SentryModule.captureMessage(message, level);
        }
      }).catch(() => {
        console.log(`[${level.toUpperCase()}]`, message);
      });
    }
  } else {
    console.log(`[${level.toUpperCase()}]`, message);
  }
}

/**
 * Set user context for error tracking
 */
export function setUserContext(userId: string, email?: string, username?: string) {
  if (!errorTrackingEnabled || !sentryInitialized) {
    return;
  }

  const Sentry = (window as any).__sentry;
  if (Sentry && Sentry.setUser) {
    Sentry.setUser({
      id: userId,
      email,
      username,
    });
  } else {
    import('@sentry/react').then((SentryModule) => {
      if (SentryModule && SentryModule.setUser) {
        SentryModule.setUser({
          id: userId,
          email,
          username,
        });
      }
    }).catch(() => {
      // Sentry not available
    });
  }
}

/**
 * Clear user context
 */
export function clearUserContext() {
  if (!errorTrackingEnabled || !sentryInitialized) {
    return;
  }

  const Sentry = (window as any).__sentry;
  if (Sentry && Sentry.setUser) {
    Sentry.setUser(null);
  } else {
    import('@sentry/react').then((SentryModule) => {
      if (SentryModule && SentryModule.setUser) {
        SentryModule.setUser(null);
      }
    }).catch(() => {
      // Sentry not available
    });
  }
}

