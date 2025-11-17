/**
 * Theme Hook
 * 
 * Manages light/dark theme state and persistence.
 */

import { useState, useEffect } from 'react';

type Theme = 'light' | 'dark';

export function useTheme() {
  const [theme, setTheme] = useState<Theme>(() => {
    try {
      // Check localStorage first
      const stored = localStorage.getItem('theme') as Theme;
      if (stored && (stored === 'light' || stored === 'dark')) {
        return stored;
      }

      // Check system preference
      if (typeof window !== 'undefined' && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        return 'dark';
      }
    } catch (error) {
      console.error('Error reading theme preference:', error);
    }

    return 'light';
  });

  useEffect(() => {
    try {
      const root = window.document.documentElement;
      
      // Remove both classes first
      root.classList.remove('light', 'dark');
      
      // Add current theme class
      root.classList.add(theme);
      
      // Store in localStorage
      localStorage.setItem('theme', theme);
    } catch (error) {
      console.error('Error setting theme:', error);
    }
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'light' ? 'dark' : 'light'));
  };

  return { theme, setTheme, toggleTheme };
}

