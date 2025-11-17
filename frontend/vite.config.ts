import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'
import { existsSync } from 'fs'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react({
      // Ensure React Fast Refresh uses the same React instance
      jsxRuntime: 'automatic',
    }),
  ],
  resolve: {
    alias: {
      // Force single React instance - use absolute paths
      // This ensures all imports resolve to the same React instance
      'react': path.resolve(__dirname, './node_modules/react'),
      'react-dom': path.resolve(__dirname, './node_modules/react-dom'),
      'react/jsx-runtime': path.resolve(__dirname, './node_modules/react/jsx-runtime'),
      'react/jsx-dev-runtime': path.resolve(__dirname, './node_modules/react/jsx-dev-runtime'),
      // Stub optional dependencies only if they don't exist
      ...(existsSync(path.resolve(__dirname, './node_modules/@sentry/react'))
        ? {}
        : { '@sentry/react': path.resolve(__dirname, './src/utils/sentry-stub.ts') }),
      ...(existsSync(path.resolve(__dirname, './node_modules/web-vitals'))
        ? {}
        : { 'web-vitals': path.resolve(__dirname, './src/utils/web-vitals-stub.ts') }),
    },
    // Deduplicate React to prevent multiple instances
    dedupe: ['react', 'react-dom', 'react-router-dom', 'react/jsx-runtime', 'react/jsx-dev-runtime'],
  },
  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      'react/jsx-runtime',
      'react/jsx-dev-runtime',
      'react-router-dom',
    ],
    // Exclude optional dependencies that may not be installed
    exclude: ['@sentry/react', 'web-vitals'],
    // Force re-optimization to ensure single React instance
    force: true,
    esbuildOptions: {
      // Ensure React is treated as external during optimization
      define: {
        global: 'globalThis',
      },
    },
  },
  ssr: {
    // Don't externalize React in SSR mode (if used)
    noExternal: ['react', 'react-dom'],
  },
  server: {
    port: 3000,
    strictPort: false, // Allow port increment if 3000 is taken
    host: true, // Listen on all addresses
    hmr: {
      // Fix HMR WebSocket connection when port is auto-incremented
      // Use the actual server port (will be auto-detected)
      port: 3000, // Match the server port
      clientPort: 3000, // Client-side port for HMR
    },
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: process.env.NODE_ENV === 'production' ? false : true, // Disable sourcemaps in production for smaller bundles
    minify: 'esbuild', // Faster than terser
    cssMinify: true,
    cssCodeSplit: true,
    target: 'esnext',
    reportCompressedSize: true,
    chunkSizeWarningLimit: 1000,
    commonjsOptions: {
      include: [/node_modules/],
      transformMixedEsModules: true,
    },
    rollupOptions: {
      output: {
        manualChunks: (id) => {
          // React vendor chunk
          if (id.includes('react') || id.includes('react-dom') || id.includes('react-router-dom')) {
            return 'react-vendor';
          }
          // Plotly chunk (large library)
          if (id.includes('plotly.js')) {
            return 'plotly-vendor';
          }
          // UI libraries chunk
          if (id.includes('@headlessui') || id.includes('@heroicons')) {
            return 'ui-vendor';
          }
          // Large node_modules go to vendor chunk
          if (id.includes('node_modules')) {
            return 'vendor';
          }
        },
        // Optimize chunk file names
        chunkFileNames: 'assets/js/[name]-[hash].js',
        entryFileNames: 'assets/js/[name]-[hash].js',
        assetFileNames: (assetInfo) => {
          const info = assetInfo.name?.split('.') || [];
          const ext = info[info.length - 1];
          if (/png|jpe?g|svg|gif|tiff|bmp|ico/i.test(ext)) {
            return `assets/images/[name]-[hash][extname]`;
          }
          if (/woff2?|eot|ttf|otf/i.test(ext)) {
            return `assets/fonts/[name]-[hash][extname]`;
          }
          return `assets/[ext]/[name]-[hash][extname]`;
        },
      },
      // Tree-shaking optimization
      treeshake: {
        preset: 'recommended',
        moduleSideEffects: false,
      },
    },
  },
})
