import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8007',
        changeOrigin: true,
        timeout: 900000,
        proxyTimeout: 900000,
      },
      '/ws': {
        target: 'ws://localhost:8007',
        ws: true,
        changeOrigin: true,
        timeout: 900000,
        proxyTimeout: 900000,
      },
    },
  },
  build: { outDir: 'dist', emptyOutDir: true },
})
