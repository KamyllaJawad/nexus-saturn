import { createRouter, createWebHashHistory } from 'vue-router'

// Rotas com # (/#/bordo): funcionam em qualquer hospedagem estática (Vercel) e
// servidas pelo FastAPI, sem precisar de fallback de SPA no servidor.
const router = createRouter({
  history: createWebHashHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', name: 'sala', component: () => import('../views/SalaView.vue') },
    { path: '/bordo', name: 'bordo', component: () => import('../views/PainelBordoView.vue') },
    { path: '/relogio', name: 'relogio', component: () => import('../views/RelogioView.vue') },
    { path: '/houston', name: 'houston', component: () => import('../views/HoustonView.vue') },
    { path: '/familia', name: 'familia', component: () => import('../views/FamiliaView.vue') },
    { path: '/dados-ia', name: 'dados-ia', component: () => import('../views/DadosIaView.vue') },
    { path: '/:qualquer(.*)', redirect: '/' },
  ],
})

export default router
