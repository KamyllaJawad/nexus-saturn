import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

// https://vite.dev/config/
export default defineConfig({
  // O build vai para 9-frontend/v2, que a API (8-backend) já serve em /v2/.
  base: '/v2/',
  build: {
    outDir: fileURLToPath(new URL('../v2', import.meta.url)),
    emptyOutDir: true,
  },
  server: {
    // Em `npm run dev`, /api vai para a API local, como nas telas servidas pela porta 8000.
    proxy: { '/api': 'http://127.0.0.1:8000' },
  },
  plugins: [vue(), vueDevTools()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
})
