/**
 * Web Vitals Performance Monitoring
 * Tracks Core Web Vitals and other performance metrics
 */

export interface WebVitalsMetric {
  name: string;
  value: number;
  rating: 'good' | 'needs-improvement' | 'poor';
  delta: number;
  id: string;
  navigationType: string;
}

type MetricHandler = (metric: WebVitalsMetric) => void;

let analyticsEnabled = false;
let metricHandlers: MetricHandler[] = [];

/**
 * Initialize Web Vitals monitoring
 */
export function initWebVitals(onMetric?: MetricHandler) {
  // Only run in browser environment
  if (typeof window === 'undefined') {
    return;
  }

  if (onMetric) {
    metricHandlers.push(onMetric);
  }

  // Check if analytics is enabled
  analyticsEnabled = import.meta.env.VITE_ENABLE_ANALYTICS === 'true';

  // Dynamically import web-vitals to avoid including it in bundle if not needed
  // Only attempt import if analytics is enabled
  if (analyticsEnabled) {
    import('web-vitals')
      .then((webVitals) => {
        // Check if web-vitals exports are available and not stubs
        const onCLSFunction = webVitals?.onCLS?.toString() || '';
        const isRealImplementation = onCLSFunction.length > 50; // Stub is just "() => {}"
        
        if (webVitals && typeof webVitals.onCLS === 'function' && isRealImplementation) {
          const { onCLS, onFID, onFCP, onLCP, onTTFB, onINP } = webVitals;
          onCLS(sendToAnalytics);
          onFID(sendToAnalytics);
          onFCP(sendToAnalytics);
          onLCP(sendToAnalytics);
          onTTFB(sendToAnalytics);
          onINP(sendToAnalytics);
        }
        // If stubs are loaded, silently skip (package not installed)
      })
      .catch(() => {
        // web-vitals not installed, skip silently
        // This is expected if the package is not installed
      });
  }
}

/**
 * Send metric to analytics and custom handlers
 */
function sendToAnalytics(metric: WebVitalsMetric) {
  // Send to all registered handlers
  metricHandlers.forEach(handler => {
    try {
      handler(metric);
    } catch (error) {
      console.error('Error in metric handler:', error);
    }
  });

  // Send to analytics if enabled
  if (analyticsEnabled && typeof window !== 'undefined') {
    // Example: Send to analytics service
    // You can integrate with Google Analytics, Plausible, or custom analytics
    const analyticsId = import.meta.env.VITE_ANALYTICS_ID;
    if (analyticsId) {
      // Custom analytics implementation
      console.log('Web Vital:', metric.name, metric.value, metric.rating);
    }
  }
}

/**
 * Measure custom performance metric
 */
export function measurePerformance(name: string, fn: () => void | Promise<void>) {
  if (typeof window === 'undefined' || !window.performance) {
    return fn();
  }

  const startMark = `${name}-start`;
  const endMark = `${name}-end`;
  const measureName = `${name}-duration`;

  performance.mark(startMark);
  
  const result = fn();
  
  if (result instanceof Promise) {
    return result.finally(() => {
      performance.mark(endMark);
      performance.measure(measureName, startMark, endMark);
      const measure = performance.getEntriesByName(measureName)[0];
      if (measure) {
        sendToAnalytics({
          name: measureName,
          value: measure.duration,
          rating: measure.duration < 100 ? 'good' : measure.duration < 300 ? 'needs-improvement' : 'poor',
          delta: measure.duration,
          id: measureName,
          navigationType: 'custom',
        });
      }
    });
  } else {
    performance.mark(endMark);
    performance.measure(measureName, startMark, endMark);
    const measure = performance.getEntriesByName(measureName)[0];
    if (measure) {
      sendToAnalytics({
        name: measureName,
        value: measure.duration,
        rating: measure.duration < 100 ? 'good' : measure.duration < 300 ? 'needs-improvement' : 'poor',
        delta: measure.duration,
        id: measureName,
        navigationType: 'custom',
      });
    }
  }

  return result;
}

/**
 * Get performance metrics summary
 */
export function getPerformanceSummary(): Record<string, number> {
  if (typeof window === 'undefined' || !window.performance) {
    return {};
  }

  const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
  if (!navigation) {
    return {};
  }

  return {
    dns: navigation.domainLookupEnd - navigation.domainLookupStart,
    tcp: navigation.connectEnd - navigation.connectStart,
    request: navigation.responseStart - navigation.requestStart,
    response: navigation.responseEnd - navigation.responseStart,
    domProcessing: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
    load: navigation.loadEventEnd - navigation.loadEventStart,
    total: navigation.loadEventEnd - navigation.fetchStart,
  };
}

