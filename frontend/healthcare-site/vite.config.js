import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { visualizer } from 'rollup-plugin-visualizer';

export default defineConfig({
  plugins: [
    react(),
    visualizer({
      filename: 'dist/stats-treemap.html',
      title: 'MediCare+ Bundle Analysis',
      template: 'treemap',     // treemap | sunburst | network
      gzipSize: true,
      brotliSize: true,
      open: false,              // don't auto-open in CI
    }),
  ],
  server: {
    port: 5174,
    open: true,
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    rollupOptions: {
      output: {
        // Manual chunks for shared dependencies
        manualChunks(id) {
          // Vendor chunk for React + ReactDOM + React Router
          if (id.includes('node_modules/react') || id.includes('node_modules/react-dom') || id.includes('node_modules/react-router') || id.includes('node_modules/@remix-run')) {
            return 'vendor-react';
          }
          // Everything else in node_modules gets a shared vendor chunk
          if (id.includes('node_modules')) {
            return 'vendor';
          }
        },
      },
    },
  },
});
