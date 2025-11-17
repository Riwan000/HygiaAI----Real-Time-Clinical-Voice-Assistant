import { ReactNode } from 'react';

/**
 * Mock ThemeProvider for tests
 * Does not require actual theme logic
 */
export function ThemeProvider({ children }: { children: ReactNode }) {
  return <>{children}</>;
}

