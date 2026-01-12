import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    react({
      // Enable Fast Refresh for React components
      fastRefresh: true,
      // Include .jsx files in the build
      include: '**/*.{jsx,tsx}',
    }),
  ],

  // Development server configuration
  server: {
    // Port for the development server
    port: 3000,
    // Automatically open browser on server start
    open: true,
    // Enable CORS for development
    cors: true,
    // Host configuration for network access
    host: true,
    // Strict port - fail if port is already in use
    strictPort: false,

    // Proxy configuration for API requests
    // This forwards /api requests to the FastAPI backend
    proxy: {
      '/api': {
        // Target FastAPI backend server
        target: 'http://localhost:8000',
        // Change origin header to match target
        changeOrigin: true,
        // Enable secure connections (set to false for self-signed certs)
        secure: false,
        // WebSocket support for real-time features
        ws: true,
        // Configure proxy to handle CORS preflight requests
        configure: (proxy, _options) => {
          proxy.on('error', (err, _req, _res) => {
            console.log('Proxy error:', err);
          });
          proxy.on('proxyReq', (proxyReq, req, _res) => {
            console.log('Proxying:', req.method, req.url, '->', proxyReq.path);
          });
          proxy.on('proxyRes', (proxyRes, req, _res) => {
            console.log('Received:', proxyRes.statusCode, req.url);
          });
        },
      },
    },

    // Hot Module Replacement configuration
    hmr: {
      // Overlay for displaying errors
      overlay: true,
    },
  },

  // Preview server configuration (for production preview)
  preview: {
    port: 3000,
    open: true,
    cors: true,
    // Proxy also works in preview mode
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
    },
  },

  // Build configuration
  build: {
    // Output directory for production build
    outDir: 'dist',
    // Directory for static assets
    assetsDir: 'assets',
    // Generate source maps for debugging
    sourcemap: true,
    // Minification settings
    minify: 'terser',
    terserOptions: {
      compress: {
        // Remove console.log in production
        drop_console: true,
        drop_debugger: true,
      },
    },
    // Rollup options for advanced bundling
    rollupOptions: {
      output: {
        // Manual chunk splitting for better caching
        manualChunks: {
          // Vendor chunk for React libraries
          vendor: ['react', 'react-dom', 'react-router-dom'],
          // UI chunk for UI-related libraries
          ui: ['@heroicons/react'],
          // Utils chunk for utility libraries
          utils: ['axios', 'date-fns'],
        },
        // Asset file naming
        assetFileNames: (assetInfo) => {
          const info = assetInfo.name.split('.');
          const ext = info[info.length - 1];
          if (/png|jpe?g|svg|gif|tiff|bmp|ico/i.test(ext)) {
            return `assets/images/[name]-[hash][extname]`;
          }
          if (/woff|woff2|eot|ttf|otf/i.test(ext)) {
            return `assets/fonts/[name]-[hash][extname]`;
          }
          return `assets/[name]-[hash][extname]`;
        },
        // Chunk file naming
        chunkFileNames: 'assets/js/[name]-[hash].js',
        // Entry file naming
        entryFileNames: 'assets/js/[name]-[hash].js',
      },
    },
    // Chunk size warning limit (in kB)
    chunkSizeWarningLimit: 1000,
    // CSS code splitting
    cssCodeSplit: true,
    // Target browsers for build
    target: 'esnext',
  },

  // Path resolution configuration
  resolve: {
    // Alias for cleaner imports
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@components': path.resolve(__dirname, './src/components'),
      '@pages': path.resolve(__dirname, './src/pages'),
      '@hooks': path.resolve(__dirname, './src/hooks'),
      '@utils': path.resolve(__dirname, './src/utils'),
      '@assets': path.resolve(__dirname, './src/assets'),
    },
    // File extensions to resolve
    extensions: ['.mjs', '.js', '.jsx', '.ts', '.tsx', '.json'],
  },

  // CSS configuration
  css: {
    // PostCSS configuration (also reads from postcss.config.js)
    postcss: './postcss.config.js',
    // CSS modules configuration
    modules: {
      // Scoped class name format
      generateScopedName: '[name]__[local]___[hash:base64:5]',
    },
    // CSS preprocessor options
    preprocessorOptions: {
      // If using SCSS
      scss: {
        additionalData: `@import "@/styles/variables.scss";`,
      },
    },
    // Enable CSS source maps in development
    devSourcemap: true,
  },

  // Optimization configuration
  optimizeDeps: {
    // Dependencies to pre-bundle
    include: [
      'react',
      'react-dom',
      'react-router-dom',
      'axios',
      '@heroicons/react/24/outline',
      '@heroicons/react/24/solid',
      'date-fns',
    ],
    // Dependencies to exclude from pre-bundling
    exclude: [],
  },

  // Environment variable configuration
  // Variables prefixed with VITE_ are exposed to client code
  envPrefix: 'VITE_',

  // Define global constants
  define: {
    // App version from package.json
    __APP_VERSION__: JSON.stringify(process.env.npm_package_version),
  },

  // ESBuild configuration
  esbuild: {
    // JSX factory function
    jsxFactory: 'React.createElement',
    // JSX fragment
    jsxFragment: 'React.Fragment',
    // Loader for .js files with JSX
    loader: 'jsx',
    include: /src\/.*\.jsx?$/,
    exclude: [],
  },

  // JSON configuration
  json: {
    // Named exports for JSON imports
    namedExports: true,
    // Stringify JSON for smaller bundle
    stringify: false,
  },

  // Logging configuration
  logLevel: 'info',
  clearScreen: true,
});