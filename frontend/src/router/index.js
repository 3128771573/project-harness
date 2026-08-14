import { createRouter, createWebHistory } from 'vue-router'

import LandingView from '../views/LandingView.vue'
import LoginView from '../views/LoginView.vue'
import RegisterView from '../views/RegisterView.vue'
import DashboardView from '../views/DashboardView.vue'
import ChatView from '../views/ChatView.vue'
import SettingsView from '../views/SettingsView.vue'
import DemoView from '../views/DemoView.vue'
import IotView from '../views/IotView.vue'
import DocsView from '../views/DocsView.vue'
import PricingView from '../views/PricingView.vue'
import StatusView from '../views/StatusView.vue'
import AdminLayout from '../layouts/AdminLayout.vue'
import AdminDashboardView from '../views/admin/AdminDashboardView.vue'
import AdminUsersView from '../views/admin/AdminUsersView.vue'
import AdminSystemView from '../views/admin/AdminSystemView.vue'
import AdminAiConfigView from '../views/admin/AdminAiConfigView.vue'
import AdminUsageView from '../views/admin/AdminUsageView.vue'
import AdminRolesView from '../views/admin/AdminRolesView.vue'
import AdminAuditView from '../views/admin/AdminAuditView.vue'
import AdminSecurityView from '../views/admin/AdminSecurityView.vue'
import AdminSettingsView from '../views/admin/AdminSettingsView.vue'
import AdminVisitsView from '../views/admin/AdminVisitsView.vue'

const routes = [
  { path: '/', name: 'home', component: LandingView },
  { path: '/login', name: 'login', component: LoginView },
  { path: '/register', name: 'register', component: RegisterView },
  { path: '/dashboard', name: 'dashboard', component: DashboardView, meta: { requiresAuth: true } },
  { path: '/ai', name: 'ai', component: ChatView, meta: { requiresAuth: true } },
  { path: '/settings', name: 'settings', component: SettingsView, meta: { requiresAuth: true } },
  { path: '/demo', name: 'demo', component: DemoView },
  { path: '/iot', name: 'iot', component: IotView },
  { path: '/docs', name: 'docs', component: DocsView },
  { path: '/pricing', name: 'pricing', component: PricingView },
  { path: '/status', name: 'status', component: StatusView },
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
      { path: 'roles', name: 'admin-roles', component: AdminRolesView },
      { path: 'audit', name: 'admin-audit', component: AdminAuditView },
      { path: 'security', name: 'admin-security', component: AdminSecurityView },
      { path: 'settings', name: 'admin-settings', component: AdminSettingsView },
      { path: 'visits', name: 'admin-visits', component: AdminVisitsView },
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

// ===== 页面访问上报（节流 2s，不记录 admin 内部路由） =====
let lastReport = 0
router.afterEach((to) => {
  const now = Date.now()
  if (now - lastReport < 2000) return
  if (to.path.startsWith('/admin')) return
  lastReport = now
  const token = localStorage.getItem('harness_access')
  const body = JSON.stringify({ path: to.path, referer: document.referrer || null })
  if (navigator.sendBeacon) {
    navigator.sendBeacon('/api/v1/system/visit', new Blob([body], { type: 'application/json' }))
  } else {
    fetch('/api/v1/system/visit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
      body,
      keepalive: true,
    }).catch(() => {})
  }
})

export default router
