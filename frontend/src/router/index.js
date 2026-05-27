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
  },
  {
    path: '/backtest',
    name: 'Backtest',
    component: () => import('../views/Backtest.vue')
  },
  {
    path: '/portfolio',
    name: 'Portfolio',
    component: () => import('../views/Portfolio.vue')
  },
  {
    path: '/monitor',
    name: 'Monitor',
    component: () => import('../views/Monitor.vue')
  },
  {
    path: '/ranking',
    name: 'Ranking',
    component: () => import('../views/Ranking.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
