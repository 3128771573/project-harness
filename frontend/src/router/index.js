import { createRouter, createWebHistory } from 'vue-router'

import LoginView from '../views/LoginView.vue'
import RegisterView from '../views/RegisterView.vue'
import DashboardView from '../views/DashboardView.vue'
import ChatView from '../views/ChatView.vue'
import AdminLayout from '../layouts/AdminLayout.vue'
import AdminDashboardView from '../views/admin/AdminDashboardView.vue'
import AdminUsersView from '../views/admin/AdminUsersView.vue'
import AdminSystemView from '../views/admin/AdminSystemView.vue'
import AdminAiConfigView from '../views/admin/AdminAiConfigView.vue'
import AdminUsageView from '../views/admin/AdminUsageView.vue'

const routes = [
  { path: '/', redirect: '/dashboard' },
  { path: '/login', name: 'login', component: LoginView },
  { path: '/register', name: 'register', component: RegisterView },
  { path: '/dashboard', name: 'dashboard', component: DashboardView, meta: { requiresAuth: true } },
  { path: '/ai', name: 'ai', component: ChatView, meta: { requiresAuth: true } },
  {
    path: '/admin',
    component: AdminLayout,
    meta: { requiresAuth: true, requiresAdmin: true },
    children: [
      { path: '', redirect: '/admin/dashboard' },
      { path: 'dashboard', name: 'admin-dashboard', component: AdminDashboardView },
      { path: 'users', name: 'admin-users', component: AdminUsersView },
      { path: 'system', name: 'admin-system', component: AdminSystemView },
      { path: 'ai-config', name: 'admin-ai-config', component: AdminAiConfigView },
      { path: 'usage', name: 'admin-usage', component: AdminUsageView },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

function getUser() {
  try {
    return JSON.parse(localStorage.getItem('harness_user') || 'null')
  } catch {
    return null
  }
}

router.beforeEach((to) => {
  const token = localStorage.getItem('harness_access')
  if (to.meta.requiresAuth && !token) {
    return { name: 'login' }
  }
  // Admin 路由: 检查角色（前端拦截只是体验优化，真正的权限由后端 RBAC 保证）
  if (to.meta.requiresAdmin) {
    const user = getUser()
    if (!user || !['admin', 'super_admin'].includes(user.role)) {
      return { name: 'dashboard' }
    }
  }
  if ((to.name === 'login' || to.name === 'register') && token) {
    return { name: 'dashboard' }
  }
})

export default router
