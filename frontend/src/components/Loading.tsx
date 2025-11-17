/**
 * Loading Component
 * 
 * Reusable loading spinner and skeleton components.
 */

import { ReactNode } from 'react';

interface LoadingProps {
  size?: 'sm' | 'md' | 'lg';
  fullScreen?: boolean;
  message?: string;
}

export function Loading({ size = 'md', fullScreen = false, message }: LoadingProps) {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-8 w-8',
    lg: 'h-12 w-12',
  };

  const content = (
    <div className="flex flex-col items-center justify-center space-y-4">
      <div
        className={`${sizeClasses[size]} border-4 border-accentLight border-t-primary rounded-full animate-spin`}
        role="status"
        aria-label={message || "Loading"}
        aria-busy="true"
      />
      {message && (
        <p className="text-sm text-slate">{message}</p>
      )}
    </div>
  );

  if (fullScreen) {
    return (
      <div className="fixed inset-0 flex items-center justify-center bg-white/90 z-50">
        {content}
      </div>
    );
  }

  return <div className="py-8">{content}</div>;
}

/**
 * Skeleton Loader Component
 */
interface SkeletonProps {
  className?: string;
}

export function Skeleton({ className = '' }: SkeletonProps) {
  return (
    <div
      className={`animate-pulse bg-slate/20 rounded ${className}`}
      aria-hidden="true"
    />
  );
}

/**
 * Loading Overlay Component
 */
interface LoadingOverlayProps {
  isLoading: boolean;
  children: ReactNode;
}

export function LoadingOverlay({ isLoading, children }: LoadingOverlayProps) {
  return (
    <div className="relative">
      {children}
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-white/90 z-10 rounded">
          <Loading size="md" />
        </div>
      )}
    </div>
  );
}

