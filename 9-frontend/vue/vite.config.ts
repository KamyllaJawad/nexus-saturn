import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

// https://vite.dev/config/
//   npm run build      → dist/, na raiz do site (Vercel). A API vem de VITE_API_URL.
//   npm run build:api  → ../v2, que o FastAPI do 8-backend serve em /v2/ (caminho relativo).
export default defineConfig(({ mode }) => {
  const paraApi = mode === 'api'
  return {
    base: paraApi ? '/v2/' : '/',
    build: paraApi
      ? { outDir: fileURLToPath(new URL('../v2', import.meta.url)), emptyOutDir: true }
      : { outDir: 'dist' },
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
  }
})
