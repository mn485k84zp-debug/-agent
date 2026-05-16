import { createRouter, createWebHistory } from 'vue-router'

import AppShell from '../views/AppShell.vue'
import ChatView from '../views/ChatView.vue'
import KnowledgeBaseView from '../views/KnowledgeBaseView.vue'
import AnalyticsView from '../views/AnalyticsView.vue'
import StatusView from '../views/StatusView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      component: AppShell,
      children: [
        { path: '', redirect: '/chat' },
        { path: '/chat', component: ChatView },
        { path: '/knowledge', component: KnowledgeBaseView },
        { path: '/analytics', component: AnalyticsView },
        { path: '/status', component: StatusView }
      ]
    }
  ]
})

export default router
