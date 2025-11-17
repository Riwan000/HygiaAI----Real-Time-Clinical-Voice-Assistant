/**
 * Skip Navigation Link Component
 * 
 * Provides keyboard-accessible skip links for screen reader users
 * to bypass repetitive navigation and jump to main content.
 */

import { Link } from 'react-router-dom';

export function SkipLink() {
  return (
    <>
      {/* Skip to main content */}
      <Link
        to="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-[100] focus:px-4 focus:py-2 focus:bg-[#2563EB] focus:text-white focus:rounded-lg focus:shadow-lg focus:outline-none focus:ring-2 focus:ring-[#2563EB] focus:ring-offset-2"
        onClick={(e) => {
          e.preventDefault();
          const mainContent = document.getElementById('main-content');
          if (mainContent) {
            mainContent.focus();
            mainContent.scrollIntoView({ behavior: 'smooth', block: 'start' });
          }
        }}
      >
        Skip to main content
      </Link>
      
      {/* Skip to navigation */}
      <Link
        to="#main-navigation"
        className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-[100] focus:px-4 focus:py-2 focus:bg-[#2563EB] focus:text-white focus:rounded-lg focus:shadow-lg focus:outline-none focus:ring-2 focus:ring-[#2563EB] focus:ring-offset-2"
        onClick={(e) => {
          e.preventDefault();
          const nav = document.getElementById('main-navigation');
          if (nav) {
            nav.focus();
            nav.scrollIntoView({ behavior: 'smooth', block: 'start' });
          }
        }}
      >
        Skip to navigation
      </Link>
    </>
  );
}

