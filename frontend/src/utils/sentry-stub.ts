/**
 * Sentry Stub Module
 * 
 * This stub module is used when @sentry/react is not installed.
 * It provides empty implementations to prevent import errors.
 * 
 * When @sentry/react is installed, Vite will resolve to the actual module.
 * When not installed, these stubs prevent runtime errors.
 */

// Stub implementations - these will be replaced if @sentry/react is installed
export const init = () => {
  // No-op: Sentry not installed
};

export const captureException = () => {
  // No-op: Sentry not installed
};

export const captureMessage = () => {
  // No-op: Sentry not installed
};

export const setUser = () => {
  // No-op: Sentry not installed
};

export const browserTracingIntegration = () => ({});

export const replayIntegration = () => ({});

