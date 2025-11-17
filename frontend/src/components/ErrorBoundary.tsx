/**
 * Error Boundary Component
 * 
 * Catches React errors and displays a fallback UI.
 */

import { Component, ReactNode, ErrorInfo } from 'react';
import { ExclamationTriangleIcon } from '@heroicons/react/24/outline';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div 
          className="min-h-screen flex items-center justify-center bg-white dark:bg-primaryDark px-4"
          role="alert"
          aria-live="assertive"
          aria-atomic="true"
        >
          <div className="max-w-md w-full bg-white dark:bg-primary rounded-lg shadow-lg p-6">
            <div className="flex items-center space-x-3 mb-4">
              <ExclamationTriangleIcon className="h-8 w-8 text-red-500" aria-hidden="true" />
              <h2 className="text-xl font-semibold text-primaryDark dark:text-white font-heading">
                Something went wrong
              </h2>
            </div>
            <p className="text-slate dark:text-white/80 mb-4">
              An unexpected error occurred. Please try refreshing the page.
            </p>
            {this.state.error && (
              <details className="mb-4">
                <summary className="cursor-pointer text-sm text-slate dark:text-white/80 mb-2">
                  Error details
                </summary>
                <pre className="text-xs bg-slate/10 dark:bg-white/10 dark:text-white p-3 rounded overflow-auto font-mono">
                  {this.state.error.toString()}
                </pre>
              </details>
            )}
            <button
              onClick={() => window.location.reload()}
              className="w-full px-4 py-2 bg-primary text-white rounded-md hover:bg-primaryDark focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2"
              aria-label="Refresh page to recover from error"
            >
              Refresh Page
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

