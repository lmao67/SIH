import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true,
    proxy: {
      '/reports': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/provenance': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/classify': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      }
    }
  }
});
