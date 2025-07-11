import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { nodePolyfills } from 'vite-plugin-node-polyfills'
import { resolve } from 'path';

export default defineConfig(({ mode }) => ({
  plugins: [
    react(),
    nodePolyfills({
      globals: { Buffer: true, global: true, process: true },
      protocolImports: true
    })
  ],
  root: resolve(__dirname, 'src'),
  optimizeDeps: {
    include: ['@uiw/react-color'],
    force: true
  },
  server: {
    port: 5173,
    cors: true, // Allow Flask to access Vite assets
    hmr: {
      port: 5173
    }
  },
  build: {
    outDir: resolve(__dirname, '../panopti/server/static/dist'),
    emptyOutDir: true,
    manifest: true,
    assetsDir: '',
    minify: mode === 'debug' ? false : 'esbuild',
    sourcemap: true,
  }
}));