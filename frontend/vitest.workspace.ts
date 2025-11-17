import { defineWorkspace } from 'vitest/config';

export default defineWorkspace([
  {
    test: {
      name: 'unit',
      include: ['src/**/*.{test,spec}.{ts,tsx}'],
      environment: 'jsdom',
    },
  },
]);

