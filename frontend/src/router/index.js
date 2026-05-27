import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    redirect: '/search'
  },
  {
    path: '/search',
    name: 'FundSearch',
    component: () => import('../views/FundSearch.vue')
  },
  {
    path: '/fund/:code',
    name: 'FundDetail',
    component: () => import('../views/FundDetail.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
