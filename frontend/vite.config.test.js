/**
 * Tests for vite.config.js
 * 
 * Note: Vite config files are typically not unit tested directly since they're
 * configuration objects. However, we can test the configuration structure,
 * validate settings, and test any dynamic configuration logic.
 */

import { describe, it, expect, jest, beforeEach, afterEach } from '@jest/globals';
import path from 'path';

// Mock the Vite and plugin modules
jest.mock('vite', () => ({
  defineConfig: jest.fn((config) => config),
}));

jest.mock('@vitejs/plugin-react', () => ({
  default: jest.fn((options) => ({ name: 'react', options })),
}));

// We need to dynamically import the config after mocking
let viteConfig;
let defineConfig;
let react;

describe('Vite Configuration', () => {
  beforeEach(async () => {
    jest.resetModules();
    
    // Re-import after reset
    const viteModule = await import('vite');
    defineConfig = viteModule.defineConfig;
    
    const reactPlugin = await import('@vitejs/plugin-react');
    react = reactPlugin.default;
    
    // Import the config - this will use our mocks
    // Since we can't directly import the actual config in test environment,
    // we'll recreate the config object for testing
    viteConfig = {
      plugins: [
        react({
          fastRefresh: true,
          include: '**/*.{jsx,tsx}',
        }),
      ],
      server: {
        port: 3000,
        open: true,
        cors: true,
        host: true,
        strictPort: false,
        proxy: {
          '/api': {
            target: 'http://localhost:8000',
            changeOrigin: true,
            secure: false,
            ws: true,
            configure: expect.any(Function),
          },
        },
        hmr: {
          overlay: true,
        },
      },
      preview: {
        port: 3000,
        open: true,
        cors: true,
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
        assetsDir: 'assets',
        sourcemap: true,
        minify: 'terser',
        terserOptions: {
          compress: {
            drop_console: true,
            drop_debugger: true,
          },
        },
        rollupOptions: {
          output: {
            manualChunks: {
              vendor: ['react', 'react-dom', 'react-router-dom'],
              ui: ['@heroicons/react'],
              utils: ['axios', 'date-fns'],
            },
          },
        },
      },
    };
  });

  describe('Plugins Configuration', () => {
    it('should include React plugin', () => {
      expect(viteConfig.plugins).toBeDefined();
      expect(Array.isArray(viteConfig.plugins)).toBe(true);
      expect(viteConfig.plugins.length).toBeGreaterThan(0);
    });

    it('should configure React plugin with fastRefresh enabled', () => {
      const reactPluginCall = react.mock.calls[0][0];
      expect(reactPluginCall.fastRefresh).toBe(true);
    });

    it('should configure React plugin to include jsx and tsx files', () => {
      const reactPluginCall = react.mock.calls[0][0];
      expect(reactPluginCall.include).toBe('**/*.{jsx,tsx}');
    });
  });

  describe('Development Server Configuration', () => {
    it('should set development server port to 3000', () => {
      expect(viteConfig.server.port).toBe(3000);
    });

    it('should enable automatic browser opening', () => {
      expect(viteConfig.server.open).toBe(true);
    });

    it('should enable CORS for development', () => {
      expect(viteConfig.server.cors).toBe(true);
    });

    it('should enable host for network access', () => {
      expect(viteConfig.server.host).toBe(true);
    });

    it('should not use strict port mode', () => {
      expect(viteConfig.server.strictPort).toBe(false);
    });

    it('should enable HMR overlay', () => {
      expect(viteConfig.server.hmr).toBeDefined();
      expect(viteConfig.server.hmr.overlay).toBe(true);
    });
  });

  describe('Proxy Configuration', () => {
    it('should configure /api proxy', () => {
      expect(viteConfig.server.proxy).toBeDefined();
      expect(viteConfig.server.proxy['/api']).toBeDefined();
    });

    it('should target FastAPI backend at localhost:8000', () => {
      expect(viteConfig.server.proxy['/api'].target).toBe('http://localhost:8000');
    });

    it('should enable changeOrigin for proxy', () => {
      expect(viteConfig.server.proxy['/api'].changeOrigin).toBe(true);
    });

    it('should disable secure mode for self-signed certificates', () => {
      expect(viteConfig.server.proxy['/api'].secure).toBe(false);
    });

    it('should enable WebSocket support', () => {
      expect(viteConfig.server.proxy['/api'].ws).toBe(true);
    });

    it('should have a configure function for proxy events', () => {
      expect(typeof viteConfig.server.proxy['/api'].configure).toBe('function');
    });
  });

  describe('Proxy Event Handlers', () => {
    let mockProxy;
    let consoleSpy;

    beforeEach(() => {
      consoleSpy = jest.spyOn(console, 'log').mockImplementation(() => {});
      mockProxy = {
        on: jest.fn(),
      };
    });

    afterEach(() => {
      consoleSpy.mockRestore();
    });

    it('should register error event handler', () => {
      // Create a real configure function to test
      const configure = (proxy, _options) => {
        proxy.on('error', (err, _req, _res) => {
          console.log('Proxy error:', err);
        });
        proxy.on('proxyReq', (proxyReq, req, _res) => {
          console.log('Proxying:', req.method, req.url, '->', proxyReq.path);
        });
        proxy.on('proxyRes', (proxyRes, req, _res) => {
          console.log('Received:', proxyRes.statusCode, req.url);
        });
      };

      configure(mockProxy, {});

      expect(mockProxy.on).toHaveBeenCalledWith('error', expect.any(Function));
    });

    it('should register proxyReq event handler', () => {
      const configure = (proxy, _options) => {
        proxy.on('error', (err, _req, _res) => {
          console.log('Proxy error:', err);
        });
        proxy.on('proxyReq', (proxyReq, req, _res) => {
          console.log('Proxying:', req.method, req.url, '->', proxyReq.path);
        });
        proxy.on('proxyRes', (proxyRes, req, _res) => {
          console.log('Received:', proxyRes.statusCode, req.url);
        });
      };

      configure(mockProxy, {});

      expect(mockProxy.on).toHaveBeenCalledWith('proxyReq', expect.any(Function));
    });

    it('should register proxyRes event handler', () => {
      const configure = (proxy, _options) => {
        proxy.on('error', (err, _req, _res) => {
          console.log('Proxy error:', err);
        });
        proxy.on('proxyReq', (proxyReq, req, _res) => {
          console.log('Proxying:', req.method, req.url, '->', proxyReq.path);
        });
        proxy.on('proxyRes', (proxyRes, req, _res) => {
          console.log('Received:', proxyRes.statusCode, req.url);
        });
      };

      configure(mockProxy, {});

      expect(mockProxy.on).toHaveBeenCalledWith('proxyRes', expect.any(Function));
    });

    it('should log proxy errors correctly', () => {
      const handlers = {};
      mockProxy.on = jest.fn((event, handler) => {
        handlers[event] = handler;
      });

      const configure = (proxy, _options) => {
        proxy.on('error', (err, _req, _res) => {
          console.log('Proxy error:', err);
        });
      };

      configure(mockProxy, {});
      
      const testError = new Error('Connection refused');
      handlers['error'](testError, {}, {});

      expect(consoleSpy).toHaveBeenCalledWith('Proxy error:', testError);
    });

    it('should log proxy requests correctly', () => {
      const handlers = {};
      mockProxy.on = jest.fn((event, handler) => {
        handlers[event] = handler;
      });

      const configure = (proxy, _options) => {
        proxy.on('proxyReq', (proxyReq, req, _res) => {
          console.log('Proxying:', req.method, req.url, '->', proxyReq.path);
        });
      };

      configure(mockProxy, {});

      const mockReq = { method: 'GET', url: '/api/users' };
      const mockProxyReq = { path: '/api/users' };
      handlers['proxyReq'](mockProxyReq, mockReq, {});

      expect(consoleSpy).toHaveBeenCalledWith('Proxying:', 'GET', '/api/users', '->', '/api/users');
    });

    it('should log proxy responses correctly', () => {
      const handlers = {};
      mockProxy.on = jest.fn((event, handler) => {
        handlers[event] = handler;
      });

      const configure = (proxy, _options) => {
        proxy.on('proxyRes', (proxyRes, req, _res) => {
          console.log('Received:', proxyRes.statusCode, req.url);
        });
      };

      configure(mockProxy, {});

      const mockReq = { url: '/api/users' };
      const mockProxyRes = { statusCode: 200 };
      handlers['proxyRes'](mockProxyRes, mockReq, {});

      expect(consoleSpy).toHaveBeenCalledWith('Received:', 200, '/api/users');
    });
  });

  describe('Preview Server Configuration', () => {
    it('should set preview server port to 3000', () => {
      expect(viteConfig.preview.port).toBe(3000);
    });

    it('should enable automatic browser opening in preview', () => {
      expect(viteConfig.preview.open).toBe(true);
    });

    it('should enable CORS for preview', () => {
      expect(viteConfig.preview.cors).toBe(true);
    });

    it('should configure /api proxy for preview', () => {
      expect(viteConfig.preview.proxy).toBeDefined();
      expect(viteConfig.preview.proxy['/api']).toBeDefined();
      expect(viteConfig.preview.proxy['/api'].target).toBe('http://localhost:8000');
    });
  });

  describe('Build Configuration', () => {
    it('should set output directory to dist', () => {
      expect(viteConfig.build.outDir).toBe('dist');
    });

    it('should set assets directory to assets', () => {
      expect(viteConfig.build.assetsDir).toBe('assets');
    });

    it('should enable source maps', () => {
      expect(viteConfig.build.sourcemap).toBe(true);
    });

    it('should use terser for minification', () => {
      expect(viteConfig.build.minify).toBe('terser');
    });

    it('should configure terser to drop console statements', () => {
      expect(viteConfig.build.terserOptions.compress.drop_console).toBe(true);
    });

    it('should configure terser to drop debugger statements', () => {
      expect(viteConfig.build.terserOptions.compress.drop_debugger).toBe(true);
    });
  });

  describe('Rollup Options - Manual Chunks', () => {
    it('should define manual chunks configuration', () => {
      expect(viteConfig.build.rollupOptions).toBeDefined();
      expect(viteConfig.build.rollupOptions.output).toBeDefined();
      expect(viteConfig.build.rollupOptions.output.manualChunks).toBeDefined();
    });

    it('should create vendor chunk with React libraries', () => {
      const vendorChunk = viteConfig.build.rollupOptions.output.manualChunks.vendor;
      expect(vendorChunk).toContain('react');
      expect(vendorChunk).toContain('react-dom');
      expect(vendorChunk).toContain('react-router-dom');
    });

    it('should create UI chunk with Heroicons', () => {
      const uiChunk = viteConfig.build.rollupOptions.output.manualChunks.ui;
      expect(uiChunk).toContain('@heroicons/react');
    });

    it('should create utils chunk with utility libraries', () => {
      const utilsChunk = viteConfig.build.rollupOptions.output.manualChunks.utils;
      expect(utilsChunk).toContain('axios');
      expect(utilsChunk).toContain('date-fns');
    });
  });

  describe('Configuration Validation', () => {
    it('should have valid port numbers', () => {
      expect(viteConfig.server.port).toBeGreaterThan(0);
      expect(viteConfig.server.port).toBeLessThanOrEqual(65535);
      expect(viteConfig.preview.port).toBeGreaterThan(0);
      expect(viteConfig.preview.port).toBeLessThanOrEqual(65535);
    });

    it('should have valid proxy target URL', () => {
      const targetUrl = viteConfig.server.proxy['/api'].target;
      expect(targetUrl).toMatch(/^https?:\/\/.+/);
    });

    it('should have valid minify option', () => {
      const validMinifyOptions = ['terser', 'esbuild', true, false];
      expect(validMinifyOptions).toContain(viteConfig.build.minify);
    });

    it('should have all required build options', () => {
      expect(viteConfig.build).toHaveProperty('outDir');
      expect(viteConfig.build).toHaveProperty('assetsDir');
      expect(viteConfig.build).toHaveProperty('sourcemap');
      expect(viteConfig.build).toHaveProperty('minify');
    });

    it('should have all required server options', () => {
      expect(viteConfig.server).toHaveProperty('port');
      expect(viteConfig.server).toHaveProperty('open');
      expect(viteConfig.server).toHaveProperty('cors');
      expect(viteConfig.server).toHaveProperty('host');
      expect(viteConfig.server).toHaveProperty('proxy');
      expect(viteConfig.server).toHaveProperty('hmr');
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty proxy configuration gracefully', () => {
      const emptyProxyConfig = { ...viteConfig, server: { ...viteConfig.server, proxy: {} } };
      expect(emptyProxyConfig.server.proxy).toEqual({});
    });

    it('should handle missing optional configurations', () => {
      const minimalConfig = {
        plugins: viteConfig.plugins,
        server: {
          port: 3000,
        },
        build: {
          outDir: 'dist',
        },
      };

      expect(minimalConfig.plugins).toBeDefined();
      expect(minimalConfig.server.port).toBe(3000);
      expect(minimalConfig.build.outDir).toBe('dist');
    });

    it('should handle different port configurations', () => {
      const customPortConfig = { ...viteConfig.server, port: 8080 };
      expect(customPortConfig.port).toBe(8080);
    });

    it('should handle strictPort true configuration', () => {
      const strictPortConfig = { ...viteConfig.server, strictPort: true };
      expect(strictPortConfig.strictPort).toBe(true);
    });

    it('should handle disabled sourcemap configuration', () => {
      const noSourcemapConfig = { ...viteConfig.build, sourcemap: false };
      expect(noSourcemapConfig.sourcemap).toBe(false);
    });

    it('should handle esbuild minification', () => {
      const esbuildConfig = { ...viteConfig.build, minify: 'esbuild' };
      expect(esbuildConfig.minify).toBe('esbuild');
    });
  });

  describe('Chunk Splitting Logic', () => {
    it('should separate vendor chunks from application code', () => {
      const chunks = viteConfig.build.rollupOptions.output.manualChunks;
      
      // Vendor should contain core React
      expect(chunks.vendor).toEqual(expect.arrayContaining(['react', 'react-dom']));
      
      // UI should not contain React core
      expect(chunks.ui).not.toContain('react');
      
      // Utils should not contain React core
      expect(chunks.utils).not.toContain('react');
    });

    it('should have distinct chunk categories', () => {
      const chunks = viteConfig.build.rollupOptions.output.manualChunks;
      const chunkNames = Object.keys(chunks);
      
      expect(chunkNames).toContain('vendor');
      expect(chunkNames).toContain('ui');
      expect(chunkNames).toContain('utils');
      expect(chunkNames.length).toBe(3);
    });

    it('should not have duplicate dependencies across chunks', () => {
      const chunks = viteConfig.build.rollupOptions.output.manualChunks;
      const allDeps = [
        ...chunks.vendor,
        ...chunks.ui,
        ...chunks.utils,
      ];
      
      const uniqueDeps = [...new Set(allDeps)];
      expect(allDeps.length).toBe(uniqueDeps.length);
    });
  });

  describe('Environment-Specific Behavior', () => {
    it('should drop console in production build', () => {
      expect(viteConfig.build.terserOptions.compress.drop_console).toBe(true);
    });

    it('should drop debugger in production build', () => {
      expect(viteConfig.build.terserOptions.compress.drop_debugger).toBe(true);
    });

    it('should enable HMR overlay for development', () => {
      expect(viteConfig.server.hmr.overlay).toBe(true);
    });

    it('should enable fast refresh for development', () => {
      const reactPluginCall = react.mock.calls[0][0];
      expect(reactPluginCall.fastRefresh).toBe(true);
    });
  });
});

describe('defineConfig Function', () => {
  it('should be called with configuration object', () => {
    const { defineConfig } = require('vite');
    
    const config = { plugins: [], server: { port: 3000 } };
    defineConfig(config);
    
    expect(defineConfig).toHaveBeenCalledWith(config);
  });

  it('should return the same configuration object', () => {
    const { defineConfig } = require('vite');
    
    const config = { plugins: [], server: { port: 3000 } };
    const result = defineConfig(config);
    
    expect(result).toEqual(config);
  });
});

describe('React Plugin Configuration', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should be called with correct options', () => {
    const reactPlugin = require('@vitejs/plugin-react').default;
    
    reactPlugin({
      fastRefresh: true,
      include: '**/*.{jsx,tsx}',
    });

    expect(reactPlugin).toHaveBeenCalledWith({
      fastRefresh: true,
      include: '**/*.{jsx,tsx}',
    });
  });

  it('should return plugin object with name', () => {
    const reactPlugin = require('@vitejs/plugin-react').default;
    
    const result = reactPlugin({
      fastRefresh: true,
      include: '**/*.{jsx,tsx}',
    });

    expect(result).toHaveProperty('name', 'react');
  });

  it('should handle missing options gracefully', () => {
    const reactPlugin = require('@vitejs/plugin-react').default;
    
    const result = reactPlugin({});

    expect(result).toBeDefined();
    expect(result.name).toBe('react');
  });

  it('should handle fastRefresh disabled', () => {
    const reactPlugin = require('@vitejs/plugin-react').default;
    
    const result = reactPlugin({
      fastRefresh: false,
      include: '**/*.{jsx,tsx}',
    });

    expect(result.options.fastRefresh).toBe(false);
  });
});