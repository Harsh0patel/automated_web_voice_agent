import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  base: '/app/',
  server: {
    port: 5173,
    proxy: {
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
      },
      '/scrape': 'http://localhost:8000',
      '/pages': 'http://localhost:8000',
      '/health': 'http://localhost:8000',
    },
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    // esbuild minification has a bug with variable renaming in certain React patterns
    // ("Cannot access 'le' before initialization"). Using 'terser' fixes it.
    minify: 'terser',
  },
});
