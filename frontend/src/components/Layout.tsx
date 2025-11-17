/**
 * Main Layout Component
 * 
 * Provides the main application structure with header, sidebar, and content area.
 */

import { ReactNode } from 'react';
import { Header } from './Header';
import { Sidebar } from './Sidebar';
import { ErrorBoundary } from './ErrorBoundary';
import { SkipLink } from './SkipLink';

interface LayoutProps {
  children: ReactNode;
}

export function Layout({ children }: LayoutProps) {
  console.log('Layout rendering...');
  
  return (
    <div className="min-h-screen bg-white dark:bg-[#0F172A] transition-colors duration-300">
      <SkipLink />
      <Header />
      <div className="flex">
        <Sidebar />
        <main 
          id="main-content"
          className="flex-1 lg:ml-64 transition-all duration-300"
          role="main"
          tabIndex={-1}
        >
          <ErrorBoundary>
            <div className="p-6 md:p-8 lg:p-10">
              {children}
            </div>
          </ErrorBoundary>
        </main>
      </div>
    </div>
  );
}

