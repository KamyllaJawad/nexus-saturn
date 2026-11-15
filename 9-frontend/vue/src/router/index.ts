import { createRouter, createWebHashHistory } from 'vue-router'

// Rotas com # (/v2/#/bordo): funcionam servidas pelo FastAPI e dentro do iframe da
// sala de simulação sem precisar de fallback de SPA no servidor.
const router = createRouter({
  history: createWebHashHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', redirect: '/bordo' },
    {
      path: '/bordo',
      name: 'bordo',
      component: () => import('../views/PainelBordoView.vue'),
    },
    {
      path: '/relogio',
      name: 'relogio',
      component: () => import('../views/RelogioView.vue'),
    },
  ],
})

export default router
