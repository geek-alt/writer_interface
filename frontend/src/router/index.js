import { createRouter, createWebHistory } from 'vue-router'

export default createRouter({
  history: createWebHistory(),
  scrollBehavior: () => ({ top: 0 }),
  routes: [
    { path: '/', name: 'Dashboard', component: () => import('@/views/Dashboard.vue') },
    { path: '/project/new', name: 'ProjectCreate', component: () => import('@/views/ProjectCreate.vue') },
    { path: '/project/:id/writer', name: 'WriterStudio', component: () => import('@/views/WriterStudio.vue') },
    { path: '/project/:id/chars', name: 'CharacterManager', component: () => import('@/views/CharacterManager.vue') },
    { path: '/project/:id/world', name: 'WorldBuilder', component: () => import('@/views/WorldBuilder.vue') },
    { path: '/project/:id/review', name: 'ReviewCenter', component: () => import('@/views/ReviewCenter.vue') },
  ],
})
