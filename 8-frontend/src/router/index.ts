import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
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
